import asyncio

from sqlalchemy import select

from src.core.decorators import handle_service_exceptions
from src.core.enums import ClockStatus
from src.core.models import BaseServiceDB, GameClockDB
from src.core.models.base import Database

from ..clocks import clock_orchestrator
from ..logging_config import get_logger
from .clock_state_machine import ClockStateMachine
from .schemas import GameClockSchemaBase, GameClockSchemaCreate, GameClockSchemaUpdate


class ClockManager:
    def __init__(self) -> None:
        self.active_gameclock_matches: dict[int, asyncio.Queue] = {}
        self.clock_state_machines: dict[int, ClockStateMachine] = {}
        self.logger = get_logger("ClockManager", self)
        self.logger.debug("Initialized ClockManager")

    async def start_clock(self, gameclock_id: int, initial_value: int = 0) -> None:
        self.logger.debug("Start clock in clock manager")
        if gameclock_id not in self.active_gameclock_matches:
            self.active_gameclock_matches[gameclock_id] = asyncio.Queue()
        if gameclock_id not in self.clock_state_machines:
            self.clock_state_machines[gameclock_id] = ClockStateMachine(gameclock_id, initial_value)

    async def end_clock(self, gameclock_id: int) -> None:
        self.logger.debug("Stop clock in clock manager")
        if gameclock_id in self.active_gameclock_matches:
            del self.active_gameclock_matches[gameclock_id]
        if gameclock_id in self.clock_state_machines:
            del self.clock_state_machines[gameclock_id]

    async def update_queue_clock(self, gameclock_id: int, message: GameClockDB) -> None:
        if gameclock_id in self.active_gameclock_matches:
            self.logger.debug("Update clock in clock manager")
            queue = self.active_gameclock_matches[gameclock_id]
            await queue.put(message)

    def get_clock_state_machine(self, gameclock_id: int) -> ClockStateMachine | None:
        return self.clock_state_machines.get(gameclock_id)


class GameClockServiceDB(BaseServiceDB):
    def __init__(self, database: Database, disable_background_tasks: bool = False) -> None:
        super().__init__(database, GameClockDB)
        self.clock_manager = ClockManager()
        self.disable_background_tasks = disable_background_tasks
        self.logger = get_logger("GameClockServiceDB", self)
        self.logger.debug("Initialized GameClockServiceDB")
        self._setup_orchestrator_callbacks()

    def _setup_orchestrator_callbacks(self) -> None:
        clock_orchestrator.set_gameclock_update_callback(self.trigger_update_gameclock)
        clock_orchestrator.set_gameclock_stop_callback(self._stop_gameclock_internal)

    @handle_service_exceptions(item_name="GAMECLOCK", operation="creating")
    async def create(self, item: GameClockSchemaCreate) -> GameClockDB:
        self.logger.debug(f"Create gameclock: {item}")
        if item.match_id is not None:
            is_exist = await self.get_gameclock_by_match_id(item.match_id)
            if is_exist:
                self.logger.info(f"gameclock already exists: {is_exist}")
                return is_exist
        return await super().create(item)

    async def _stop_gameclock_internal(self, gameclock_id: int) -> None:
        """Handle gameclock stop when it reaches 0"""
        self.logger.debug(f"Stopping gameclock {gameclock_id} (reached 0)")
        clock_orchestrator.unregister_gameclock(gameclock_id)
        await self.clock_manager.end_clock(gameclock_id)
        await self.update(
            gameclock_id,
            GameClockSchemaUpdate(
                gameclock=0,
                gameclock_status="stopped",
            ),
        )

    async def stop_gameclock(self, gameclock_id: int) -> None:
        """Manually stop gameclock and unregister from orchestrator"""
        self.logger.debug(f"Manually stopping gameclock {gameclock_id}")
        state_machine = self.clock_manager.get_clock_state_machine(gameclock_id)
        if state_machine:
            state_machine.stop()
        clock_orchestrator.unregister_gameclock(gameclock_id)
        await self.clock_manager.end_clock(gameclock_id)

    async def enable_match_data_gameclock_queues(
        self,
        item_id: int,
    ) -> asyncio.Queue:
        self.logger.debug(f"Enable matchdata gameclock queues match id:{item_id}")
        gameclock = await self.get_by_id(item_id)

        if not gameclock:
            self.logger.warning(f"Gameclock not found: {item_id}")

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if item_id not in active_clock_matches:
            self.logger.debug(f"Gameclock not in active gameclock matches: {item_id}")
            initial_value = gameclock.gameclock if gameclock and gameclock.gameclock else 0
            await self.clock_manager.start_clock(item_id, initial_value)

            state_machine = self.clock_manager.get_clock_state_machine(item_id)
            if state_machine and gameclock and gameclock.gameclock_status == ClockStatus.RUNNING:
                state_machine.start()

            if state_machine and state_machine.status == ClockStatus.RUNNING:
                clock_orchestrator.register_gameclock(item_id, state_machine)

            self.logger.debug(f"Gameclock added to active gameclock matches: {item_id}")
        match_queue = active_clock_matches[item_id]
        if gameclock:
            await match_queue.put(gameclock)
        self.logger.info(f"Gameclock enabled successfully {gameclock}")
        return match_queue

    async def update(
        self,
        item_id: int,
        item: GameClockSchemaUpdate,
        **kwargs,
    ) -> GameClockDB | None:
        self.logger.debug(f"Update gameclock endpoint id:{item_id} data: {item}")
        async with self.db.get_session_maker()() as session:
            result = await session.execute(select(GameClockDB).where(GameClockDB.id == item_id))
            updated_item = result.scalars().one_or_none()

            if not updated_item:
                self.logger.warning(f"GameClock not found: {item_id}")
                return None

            update_data = item.model_dump(exclude_unset=True)
            update_data["version"] = (updated_item.version or 0) + 1

            for key, value in update_data.items():
                if value is not None or key == "started_at_ms":
                    setattr(updated_item, key, value)

            await session.flush()
            await session.commit()
            await session.refresh(updated_item)

            self.logger.debug(f"Updated gameclock: {updated_item}")
            await self.trigger_update_gameclock(item_id)

            return updated_item

    async def get_gameclock_status(
        self,
        item_id: int,
    ) -> str | None:
        self.logger.debug(f"Get gameclock status for item id:{item_id}")
        gameclock: GameClockSchemaBase = await self.get_by_id(item_id)
        if gameclock:
            self.logger.debug(f"Gameclock status: {gameclock}")
            return gameclock.gameclock_status
        else:
            self.logger.warning(f"Gameclock not found: {item_id}")
            return None

    async def get_gameclock_by_match_id(self, match_id: int) -> GameClockDB | None:
        async with self.db.get_session_maker()() as session:
            self.logger.debug(f"Get gameclock by match id:{match_id}")
            result = await session.scalars(
                select(GameClockDB).where(GameClockDB.match_id == match_id)
            )
            if result:
                self.logger.debug(f"Gameclock in DB: {result}")
                gameclock = result.one_or_none()
                if gameclock:
                    state_machine = self.clock_manager.get_clock_state_machine(gameclock.id)
                    if state_machine and state_machine.status == ClockStatus.RUNNING:
                        gameclock.gameclock = state_machine.get_current_value()
                    self.logger.debug(f"Gameclock found: {gameclock}")
                    return gameclock
        return None

    async def trigger_update_gameclock(
        self,
        gameclock_id: int,
    ) -> None:
        self.logger.debug(f"Trigger update gameclock for gameclock id:{gameclock_id}")
        gameclock: GameClockSchemaBase | None = await self.get_by_id(gameclock_id)

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if gameclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[gameclock_id]
            await matchdata_clock_queue.put(gameclock)
        else:
            self.logger.warning(f"No active gameclock found with id:{gameclock_id}")
