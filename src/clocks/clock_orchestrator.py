import asyncio
import time
from typing import Awaitable, Callable, Protocol

from src.logging_config import get_logger


class ClockStateMachineProtocol(Protocol):
    started_at_ms: int | None

    def get_current_value(self) -> int: ...


class ClockOrchestrator:
    def __init__(self) -> None:
        self.running_playclocks: dict[int, ClockStateMachineProtocol] = {}
        self.running_gameclocks: dict[int, ClockStateMachineProtocol] = {}
        self._last_updated_second: dict[int, int] = {}  # clock_id -> last second updated
        self._task: asyncio.Task | None = None
        self._is_running = False
        self._is_stopping = False
        self._playclock_update_callback: Callable[[int], Awaitable[None]] | None = None
        self._gameclock_update_callback: Callable[[int], Awaitable[None]] | None = None
        self._playclock_stop_callback: Callable[[int], Awaitable[None]] | None = None
        self._gameclock_stop_callback: Callable[[int], Awaitable[None]] | None = None
        self.logger = get_logger("ClockOrchestrator", self)
        self.logger.debug("Initialized ClockOrchestrator")

    async def start(self) -> None:
        """Start the single timer loop"""
        if self._is_running:
            self.logger.warning("ClockOrchestrator already running")
            return

        self._is_stopping = False
        self._is_running = True
        self._task = asyncio.create_task(self._run_loop())
        self.logger.info("ClockOrchestrator started")

    async def stop(self) -> None:
        """Stop the single timer loop"""
        self._is_stopping = True
        self._is_running = False
        self._playclock_update_callback = None
        self._gameclock_update_callback = None
        self._playclock_stop_callback = None
        self._gameclock_stop_callback = None
        self.running_playclocks.clear()
        self.running_gameclocks.clear()
        self._last_updated_second.clear()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                self.logger.warning("ClockOrchestrator loop stopped with error: %s", exc)
            self._task = None
        self._is_stopping = False
        self.logger.info("ClockOrchestrator stopped")

    async def _run_loop(self) -> None:
        """Single loop checking all clocks every 100ms"""
        self.logger.debug("ClockOrchestrator loop started")
        while self._is_running:
            for clock_id, state_machine in list(self.running_playclocks.items()):
                if self._should_update(clock_id, state_machine):
                    await self._update_playclock(clock_id, state_machine)

            for clock_id, state_machine in list(self.running_gameclocks.items()):
                if self._should_update(clock_id, state_machine):
                    await self._update_gameclock(clock_id, state_machine)

            await asyncio.sleep(0.1)

        self.logger.debug("ClockOrchestrator loop stopped")

    def _should_update(self, clock_id: int, state_machine: ClockStateMachineProtocol) -> bool:
        """Check if clock needs to update at this moment (once per second)"""
        if not hasattr(state_machine, "started_at_ms") or state_machine.started_at_ms is None:
            return False

        # Use time.time() to match state_machine.started_at_ms which uses time.time() * 1000
        now_ms = time.time() * 1000
        elapsed_ms = now_ms - state_machine.started_at_ms
        elapsed_sec = elapsed_ms / 1000.0
        current_second = int(elapsed_sec)

        # Only update if we haven't updated for this second yet
        last_second = self._last_updated_second.get(clock_id, -1)
        if current_second > last_second:
            self._last_updated_second[clock_id] = current_second
            return True
        return False

    async def _update_playclock(
        self, clock_id: int, state_machine: ClockStateMachineProtocol
    ) -> None:
        """Update playclock and trigger NOTIFY"""
        if self._is_stopping or not self._is_running:
            return
        current_value = state_machine.get_current_value()
        if current_value == 0:
            if self._playclock_stop_callback:
                await self._playclock_stop_callback(clock_id)
            self.unregister_playclock(clock_id)
        else:
            if self._playclock_update_callback:
                await self._playclock_update_callback(clock_id)

    async def _update_gameclock(
        self, clock_id: int, state_machine: ClockStateMachineProtocol
    ) -> None:
        """Update gameclock and trigger NOTIFY"""
        if self._is_stopping or not self._is_running:
            return
        current_value = state_machine.get_current_value()
        if current_value == 0:
            self.logger.info("Gameclock %s reached 0; stopping", clock_id)
            if self._gameclock_stop_callback:
                self.logger.debug("Invoking gameclock stop callback for %s", clock_id)
                await self._gameclock_stop_callback(clock_id)
            self.unregister_gameclock(clock_id)
        else:
            if self._gameclock_update_callback:
                await self._gameclock_update_callback(clock_id)

    def register_playclock(self, clock_id: int, state_machine: ClockStateMachineProtocol) -> None:
        """Register a playclock with the orchestrator"""
        self.running_playclocks[clock_id] = state_machine
        self.logger.debug(f"Registered playclock {clock_id}")

    def unregister_playclock(self, clock_id: int) -> None:
        """Unregister a playclock from the orchestrator"""
        self.running_playclocks.pop(clock_id, None)
        self._last_updated_second.pop(clock_id, None)
        self.logger.debug(f"Unregistered playclock {clock_id}")

    def register_gameclock(self, clock_id: int, state_machine: ClockStateMachineProtocol) -> None:
        """Register a gameclock with the orchestrator"""
        self.running_gameclocks[clock_id] = state_machine
        self.logger.debug(f"Registered gameclock {clock_id}")

    def unregister_gameclock(self, clock_id: int) -> None:
        """Unregister a gameclock from the orchestrator"""
        self.running_gameclocks.pop(clock_id, None)
        self._last_updated_second.pop(clock_id, None)
        self.logger.debug(f"Unregistered gameclock {clock_id}")

    def set_playclock_update_callback(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """Set callback for playclock updates (triggers NOTIFY)"""
        self._playclock_update_callback = callback
        self.logger.debug("Set playclock update callback")

    def set_gameclock_update_callback(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """Set callback for gameclock updates (triggers NOTIFY)"""
        self._gameclock_update_callback = callback
        self.logger.debug("Set gameclock update callback")

    def set_playclock_stop_callback(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """Set callback for playclock stop (when clock reaches 0)"""
        self._playclock_stop_callback = callback
        self.logger.debug("Set playclock stop callback")

    def set_gameclock_stop_callback(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """Set callback for gameclock stop (when clock reaches 0)"""
        self._gameclock_stop_callback = callback
        self.logger.debug("Set gameclock stop callback")
