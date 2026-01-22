import time


class ClockStateMachine:
    def __init__(self, clock_id: int, initial_value: int) -> None:
        self.clock_id = clock_id
        self.value = initial_value
        self.status = "stopped"
        self.started_at: float | None = None
        self.last_db_sync = time.time()

    def get_current_value(self) -> int:
        if self.status != "running":
            return self.value
        if self.started_at is None:
            return self.value
        elapsed = int(time.time() - self.started_at)
        return max(0, self.value - elapsed)

    def start(self) -> None:
        self.started_at = time.time()
        self.status = "running"
        self.last_db_sync = time.time()

    def stop(self) -> None:
        self.value = self.get_current_value()
        self.status = "stopped"
        self.started_at = None
        self.last_db_sync = time.time()

    def pause(self) -> None:
        self.value = self.get_current_value()
        self.status = "paused"
        self.started_at = None
        self.last_db_sync = time.time()

    def needs_db_sync(self, sync_interval_seconds: int = 5) -> bool:
        return time.time() - self.last_db_sync > sync_interval_seconds

    def mark_db_synced(self) -> None:
        self.last_db_sync = time.time()
