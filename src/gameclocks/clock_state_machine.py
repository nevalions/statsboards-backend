import time


class ClockStateMachine:
    def __init__(self, clock_id: int, initial_value: int) -> None:
        self.clock_id = clock_id
        self.value = initial_value
        self.status = "stopped"
        self.started_at_ms: int | None = None

    def get_current_value(self) -> int:
        if self.status != "running" or self.started_at_ms is None:
            return self.value
        elapsed_ms = int(time.time() * 1000) - self.started_at_ms
        elapsed_sec = elapsed_ms // 1000
        return max(0, self.value - elapsed_sec)

    def get_started_at_ms(self) -> int | None:
        return self.started_at_ms

    def start(self) -> None:
        self.started_at_ms = int(time.time() * 1000)
        self.status = "running"

    def stop(self) -> None:
        self.value = self.get_current_value()
        self.status = "stopped"
        self.started_at_ms = None

    def pause(self) -> None:
        self.value = self.get_current_value()
        self.status = "paused"
        self.started_at_ms = None
