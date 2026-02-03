import asyncio
import gc
import weakref

import pytest

from src.playclocks.clock_manager import ClockManager
from src.playclocks.clock_state_machine import ClockStateMachine

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestPlayClockManager:
    async def test_initial_state(self):
        manager = ClockManager()
        assert manager.active_playclock_matches == {}
        assert manager.clock_state_machines == {}

    async def test_start_clock_creates_queue_and_state_machine(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)

        assert 1 in manager.active_playclock_matches
        assert isinstance(manager.active_playclock_matches[1], asyncio.Queue)
        assert 1 in manager.clock_state_machines
        assert isinstance(manager.clock_state_machines[1], ClockStateMachine)
        assert manager.clock_state_machines[1].value == 100
        assert manager.clock_state_machines[1].clock_id == 1

    async def test_start_clock_default_initial_value(self):
        manager = ClockManager()
        await manager.start_clock(2)

        assert 2 in manager.clock_state_machines
        assert manager.clock_state_machines[2].value == 0

    async def test_start_clock_duplicate_id_does_not_recreate(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)
        original_queue = manager.active_playclock_matches[1]
        original_state_machine = manager.clock_state_machines[1]

        await manager.start_clock(1, 200)

        assert manager.active_playclock_matches[1] is original_queue
        assert manager.clock_state_machines[1] is original_state_machine
        assert manager.clock_state_machines[1].value == 100

    async def test_start_clock_multiple_ids(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)
        await manager.start_clock(2, 200)
        await manager.start_clock(3, 300)

        assert len(manager.active_playclock_matches) == 3
        assert len(manager.clock_state_machines) == 3
        assert manager.clock_state_machines[1].value == 100
        assert manager.clock_state_machines[2].value == 200
        assert manager.clock_state_machines[3].value == 300

    async def test_end_clock_removes_queue_and_state_machine(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)

        await manager.end_clock(1)

        assert 1 not in manager.active_playclock_matches
        assert 1 not in manager.clock_state_machines

    async def test_end_clock_non_existent_id(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)

        await manager.end_clock(999)

        assert 1 in manager.active_playclock_matches
        assert 1 in manager.clock_state_machines

    async def test_end_clock_multiple_ids(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)
        await manager.start_clock(2, 200)
        await manager.start_clock(3, 300)

        await manager.end_clock(1)
        await manager.end_clock(3)

        assert 1 not in manager.active_playclock_matches
        assert 1 not in manager.clock_state_machines
        assert 3 not in manager.active_playclock_matches
        assert 3 not in manager.clock_state_machines
        assert 2 in manager.active_playclock_matches
        assert 2 in manager.clock_state_machines

    async def test_get_clock_state_machine_existing(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)

        state_machine = manager.get_clock_state_machine(1)

        assert state_machine is not None
        assert isinstance(state_machine, ClockStateMachine)
        assert state_machine.value == 100
        assert state_machine.clock_id == 1

    async def test_get_clock_state_machine_non_existent(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)

        state_machine = manager.get_clock_state_machine(999)

        assert state_machine is None

    async def test_update_queue_clock_existing(self):
        from src.core.models import PlayClockDB

        manager = ClockManager()
        await manager.start_clock(1, 100)

        mock_playclock = PlayClockDB(id=1, playclock=95, playclock_status="running", match_id=1)
        await manager.update_queue_clock(1, mock_playclock)

        queue = manager.active_playclock_matches[1]
        result = await queue.get()
        assert result is mock_playclock

    async def test_update_queue_clock_non_existent_id(self):
        from src.core.models import PlayClockDB

        manager = ClockManager()
        await manager.start_clock(1, 100)

        mock_playclock = PlayClockDB(id=999, playclock=95, playclock_status="running", match_id=999)

        await manager.update_queue_clock(999, mock_playclock)

        queue = manager.active_playclock_matches[1]
        assert queue.empty()

    async def test_lifecycle_start_update_end(self):
        from src.core.models import PlayClockDB

        manager = ClockManager()
        match_id = 1

        await manager.start_clock(match_id, 100)
        assert match_id in manager.active_playclock_matches

        mock_playclock = PlayClockDB(
            id=1, playclock=95, playclock_status="running", match_id=match_id
        )
        await manager.update_queue_clock(match_id, mock_playclock)
        queue = manager.active_playclock_matches[match_id]
        result = await queue.get()
        assert result is mock_playclock

        await manager.end_clock(match_id)
        assert match_id not in manager.active_playclock_matches

    async def test_multiple_state_machines_independent(self):
        manager = ClockManager()
        await manager.start_clock(1, 100)
        await manager.start_clock(2, 200)

        sm1 = manager.get_clock_state_machine(1)
        sm2 = manager.get_clock_state_machine(2)

        assert sm1 is not None
        assert sm2 is not None

        sm1.start()
        assert sm1.status == "running"
        assert sm2.status == "stopped"

        sm2.start()
        assert sm1.status == "running"
        assert sm2.status == "running"

        sm1.stop()
        assert sm1.status == "stopped"
        assert sm2.status == "running"

    async def test_end_clock_releases_references(self):
        manager = ClockManager()
        match_id = 1

        await manager.start_clock(match_id, 100)
        state_machine = manager.get_clock_state_machine(match_id)
        queue = manager.active_playclock_matches[match_id]

        assert state_machine is not None

        state_machine_ref = weakref.ref(state_machine)
        queue_ref = weakref.ref(queue)

        await manager.end_clock(match_id)
        del state_machine
        del queue

        gc.collect()

        assert match_id not in manager.active_playclock_matches
        assert match_id not in manager.clock_state_machines
        assert state_machine_ref() is None
        assert queue_ref() is None

    async def test_end_clock_drains_queue_with_pending_messages(self):
        from src.core.models import PlayClockDB

        manager = ClockManager()
        match_id = 1

        await manager.start_clock(match_id, 100)

        queue = manager.active_playclock_matches[match_id]

        for i in range(5):
            mock_playclock = PlayClockDB(
                id=i, playclock=100 - i * 5, playclock_status="running", match_id=match_id
            )
            await manager.update_queue_clock(match_id, mock_playclock)

        assert queue.qsize() == 5

        await manager.end_clock(match_id)

        assert match_id not in manager.active_playclock_matches
        assert match_id not in manager.clock_state_machines

    async def test_end_clock_memory_leak_prevention(self):
        from src.core.models import PlayClockDB

        manager = ClockManager()
        match_id = 1

        await manager.start_clock(match_id, 100)

        queue = manager.active_playclock_matches[match_id]

        for i in range(10):
            mock_playclock = PlayClockDB(
                id=i, playclock=100 - i, playclock_status="running", match_id=match_id
            )
            await manager.update_queue_clock(match_id, mock_playclock)

        queue_ref = weakref.ref(queue)

        await manager.end_clock(match_id)
        del queue
        gc.collect()

        assert match_id not in manager.active_playclock_matches
        assert queue_ref() is None
