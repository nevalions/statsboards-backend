import asyncio

from src.core.models import PlayClockDB
from src.logging_config import get_logger


class ClockManager:
    def __init__(self) -> None:
        self.active_playclock_matches: dict[int, asyncio.Queue] = {}
        self.logger = get_logger("backend_logger_ClockManager", self)
        self.logger.debug("Initialized ClockManager")

    async def start_clock(self, match_id: int) -> None:
        self.logger.debug("Start clock in clock manager")
        if match_id not in self.active_playclock_matches:
            self.active_playclock_matches[match_id] = asyncio.Queue()

    async def end_clock(self, match_id: int) -> None:
        if match_id in self.active_playclock_matches:
            self.logger.debug("Stop clock in clock manager")
            del self.active_playclock_matches[match_id]

    async def update_queue_clock(self, match_id: int, message: PlayClockDB) -> None:
        if match_id in self.active_playclock_matches:
            self.logger.debug("Update clock in clock manager")
            queue = self.active_playclock_matches[match_id]
            await queue.put(message)
