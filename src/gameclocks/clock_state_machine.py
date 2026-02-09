import time

from src.core.enums import ClockDirection, ClockStatus


class ClockStateMachine:
    def __init__(
        self,
        clock_id: int,
        initial_value: int,
        direction: ClockDirection = ClockDirection.DOWN,
        max_value: int = 720,
    ) -> None:
        self.clock_id = clock_id
        self.value = initial_value
        self.direction = direction
        self.max_value = max_value
        self.status = ClockStatus.STOPPED
        self.started_at_ms: int | None = None

    def get_current_value(self) -> int:
        if self.status != ClockStatus.RUNNING or self.started_at_ms is None:
            return self.value
        elapsed_ms = int(time.time() * 1000) - self.started_at_ms
        elapsed_sec = elapsed_ms // 1000

        if self.direction == ClockDirection.DOWN:
            return max(0, self.value - elapsed_sec)
        else:
            return min(self.max_value, self.value + elapsed_sec)

    def get_started_at_ms(self) -> int | None:
        return self.started_at_ms

    def start(self) -> None:
        self.started_at_ms = int(time.time() * 1000)
        self.status = ClockStatus.RUNNING

    def stop(self) -> None:
        self.value = self.get_current_value()
        self.status = ClockStatus.STOPPED
        self.started_at_ms = None

    def pause(self) -> None:
        self.value = self.get_current_value()
        self.status = ClockStatus.PAUSED
        self.started_at_ms = None
