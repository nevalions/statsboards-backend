import asyncio

from src.gameclocks.clock_state_machine import ClockStateMachine


class TestClockStateMachine:
    """Test gameclock state machine behavior - pause/resume/stop operations."""

    def test_pause_preserves_current_value(self):
        """Test that pausing a running state machine preserves current value."""
        state_machine = ClockStateMachine(1, 720)
        assert state_machine.status == "stopped"
        assert state_machine.value == 720

        state_machine.start()
        assert state_machine.status == "running"
        assert state_machine.started_at_ms is not None

        state_machine.pause()
        assert state_machine.status == "paused"
        assert state_machine.started_at_ms is None

        paused_value = state_machine.get_current_value()
        assert paused_value == 720

    def test_resume_from_paused_continues_from_paused_value(self):
        """Test that resuming from paused continues from paused value."""
        state_machine = ClockStateMachine(1, 720)
        assert state_machine.status == "stopped"

        state_machine.start()
        asyncio.run(asyncio.sleep(0.1))
        current_value_1 = state_machine.get_current_value()

        state_machine.pause()
        paused_value = state_machine.get_current_value()
        assert state_machine.status == "paused"

        asyncio.run(asyncio.sleep(0.1))

        state_machine.start()
        assert state_machine.status == "running"
        assert state_machine.started_at_ms is not None

        asyncio.run(asyncio.sleep(0.1))
        current_value_2 = state_machine.get_current_value()

    def test_stop_does_not_override_paused_status(self):
        """Test that stop() sets status to stopped regardless of previous state."""
        state_machine = ClockStateMachine(1, 720)
        assert state_machine.status == "stopped"

        state_machine.start()
        asyncio.run(asyncio.sleep(0.1))
        current_value = state_machine.get_current_value()

        state_machine.pause()
        paused_value = state_machine.get_current_value()
        assert state_machine.status == "paused"

        state_machine.stop()
        assert state_machine.status == "stopped"
        assert state_machine.get_current_value() == paused_value

    def test_calculate_elapsed_time_from_started_at_ms(self):
        """Test that get_current_value calculates elapsed time correctly."""
        state_machine = ClockStateMachine(1, 720)
        assert state_machine.value == 720
        assert state_machine.status == "stopped"

        state_machine.start()
        asyncio.run(asyncio.sleep(0.1))
        current_value_1 = state_machine.get_current_value()
        elapsed_time_1 = 720 - current_value_1
        assert elapsed_time_1 >= 0

        asyncio.run(asyncio.sleep(0.2))
        current_value_2 = state_machine.get_current_value()
        elapsed_time_2 = 720 - current_value_2
        assert elapsed_time_2 >= elapsed_time_1
        assert elapsed_time_2 <= 0.3
