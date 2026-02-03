import asyncio

from src.core.models import PlayClockDB
from src.logging_config import get_logger

from .clock_state_machine import ClockStateMachine


class ClockManager:
    def __init__(self) -> None:
        self.active_playclock_matches: dict[int, asyncio.Queue] = {}
        self.clock_state_machines: dict[int, ClockStateMachine] = {}
        self.logger = get_logger("ClockManager", self)
        self.logger.debug("Initialized ClockManager")

    async def start_clock(self, match_id: int, initial_value: int = 0) -> None:
        self.logger.debug("Start clock in clock manager")
        if match_id not in self.active_playclock_matches:
            self.active_playclock_matches[match_id] = asyncio.Queue()
        if match_id not in self.clock_state_machines:
            self.clock_state_machines[match_id] = ClockStateMachine(match_id, initial_value)

    async def end_clock(self, match_id: int) -> None:
        if match_id in self.active_playclock_matches:
            self.logger.debug("Stop clock in clock manager")
            queue = self.active_playclock_matches[match_id]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            del self.active_playclock_matches[match_id]
        if match_id in self.clock_state_machines:
            del self.clock_state_machines[match_id]

    async def update_queue_clock(self, match_id: int, message: PlayClockDB) -> None:
        if match_id in self.active_playclock_matches:
            self.logger.debug("Update clock in clock manager")
            queue = self.active_playclock_matches[match_id]
            await queue.put(message)

    def get_clock_state_machine(self, match_id: int) -> ClockStateMachine | None:
        return self.clock_state_machines.get(match_id)
