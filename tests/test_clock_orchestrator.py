import gc
import time
import weakref

from src.clocks.clock_orchestrator import ClockOrchestrator


class FakeStateMachine:
    def __init__(self, started_at_ms: int) -> None:
        self.started_at_ms = started_at_ms

    def get_current_value(self) -> int:
        return 1


class TestClockOrchestrator:
    async def test_start_stop_clears_task(self):
        orchestrator = ClockOrchestrator()

        await orchestrator.start()
        assert orchestrator._task is not None
        assert orchestrator._is_running is True

        await orchestrator.stop()
        assert orchestrator._task is None
        assert orchestrator._is_running is False

    def test_unregister_playclock_releases_references(self):
        orchestrator = ClockOrchestrator()
        clock_id = 1
        state_machine = FakeStateMachine(int(time.time() * 1000) - 1500)

        orchestrator.register_playclock(clock_id, state_machine)
        assert orchestrator._should_update(clock_id, state_machine) is True
        assert clock_id in orchestrator.running_playclocks
        assert clock_id in orchestrator._last_updated_second

        state_machine_ref = weakref.ref(state_machine)
        orchestrator.unregister_playclock(clock_id)
        del state_machine

        gc.collect()

        assert clock_id not in orchestrator.running_playclocks
        assert clock_id not in orchestrator._last_updated_second
        assert state_machine_ref() is None

    def test_unregister_gameclock_releases_references(self):
        orchestrator = ClockOrchestrator()
        clock_id = 2
        state_machine = FakeStateMachine(int(time.time() * 1000) - 1500)

        orchestrator.register_gameclock(clock_id, state_machine)
        assert orchestrator._should_update(clock_id, state_machine) is True
        assert clock_id in orchestrator.running_gameclocks
        assert clock_id in orchestrator._last_updated_second

        state_machine_ref = weakref.ref(state_machine)
        orchestrator.unregister_gameclock(clock_id)
        del state_machine

        gc.collect()

        assert clock_id not in orchestrator.running_gameclocks
        assert clock_id not in orchestrator._last_updated_second
        assert state_machine_ref() is None
