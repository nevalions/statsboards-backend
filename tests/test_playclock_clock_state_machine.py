import time

from src.playclocks.clock_state_machine import ClockStateMachine


class TestClockStateMachine:
    def test_initial_state(self):
        state_machine = ClockStateMachine(1, 100)
        assert state_machine.clock_id == 1
        assert state_machine.value == 100
        assert state_machine.status == "stopped"
        assert state_machine.started_at_ms is None
        assert isinstance(state_machine.last_db_sync, float)

    def test_get_current_value_stopped(self):
        state_machine = ClockStateMachine(1, 100)
        assert state_machine.get_current_value() == 100

    def test_get_current_value_running(self):
        state_machine = ClockStateMachine(1, 100)
        state_machine.start()
        time.sleep(1)
        current_value = state_machine.get_current_value()
        assert current_value == 99
        time.sleep(1)
        current_value = state_machine.get_current_value()
        assert current_value == 98

    def test_get_current_value_does_not_go_below_zero(self):
        state_machine = ClockStateMachine(1, 2)
        state_machine.start()
        time.sleep(3)
        current_value = state_machine.get_current_value()
        assert current_value == 0

    def test_start(self):
        state_machine = ClockStateMachine(1, 100)
        state_machine.start()
        assert state_machine.status == "running"
        assert state_machine.started_at_ms is not None

    def test_stop(self):
        state_machine = ClockStateMachine(1, 100)
        state_machine.start()
        time.sleep(2)
        state_machine.stop()
        assert state_machine.status == "stopped"
        assert state_machine.started_at_ms is None
        assert state_machine.value == 98

    def test_pause(self):
        state_machine = ClockStateMachine(1, 100)
        state_machine.start()
        time.sleep(2)
        state_machine.pause()
        assert state_machine.status == "paused"
        assert state_machine.started_at_ms is None
        assert state_machine.value == 98

    def test_needs_db_sync(self):
        state_machine = ClockStateMachine(1, 100)
        assert not state_machine.needs_db_sync(5)

    def test_needs_db_sync_after_interval(self):
        state_machine = ClockStateMachine(1, 100)
        time.sleep(1)
        assert state_machine.needs_db_sync(0.5)
        assert not state_machine.needs_db_sync(5)

    def test_mark_db_synced(self):
        state_machine = ClockStateMachine(1, 100)
        time.sleep(1)
        assert state_machine.needs_db_sync(0.5)
        state_machine.mark_db_synced()
        assert not state_machine.needs_db_sync(0.5)

    def test_full_lifecycle(self):
        state_machine = ClockStateMachine(1, 100)
        assert state_machine.get_current_value() == 100

        state_machine.start()
        time.sleep(2)
        current_value = state_machine.get_current_value()
        assert 97 <= current_value <= 98

        state_machine.stop()
        assert state_machine.status == "stopped"
        assert state_machine.value == current_value

        state_machine.start()
        time.sleep(1)
        current_value = state_machine.get_current_value()
        assert state_machine.value - 1 <= current_value <= state_machine.value

        state_machine.pause()
        assert state_machine.status == "paused"
        paused_value = state_machine.get_current_value()

        state_machine.start()
        time.sleep(1)
        assert state_machine.get_current_value() == paused_value - 1
