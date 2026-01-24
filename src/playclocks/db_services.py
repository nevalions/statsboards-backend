import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayClockDB, handle_service_exceptions
from src.core.models.base import Database

from ..clocks import clock_orchestrator
from ..logging_config import get_logger
from .clock_manager import ClockManager
from .schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate

ITEM = "PLAYCLOCK"


class PlayClockServiceDB(BaseServiceDB):
    def __init__(self, database: Database, disable_background_tasks: bool = False) -> None:
        super().__init__(database, PlayClockDB)
        self.clock_manager = ClockManager()
        self.disable_background_tasks = disable_background_tasks
        self.logger = get_logger("backend_logger_PlayClockServiceDB", self)
        self.logger.debug("Initialized PlayClockServiceDB")
        self._setup_orchestrator_callbacks()

    def _setup_orchestrator_callbacks(self) -> None:
        clock_orchestrator.set_playclock_update_callback(self.trigger_update_playclock)
        clock_orchestrator.set_playclock_stop_callback(self._stop_playclock_internal)

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: PlayClockSchemaCreate) -> PlayClockDB:
        self.logger.debug(f"Create playclock: {item}")
        if item.match_id is not None:
            is_exist = await self.get_playclock_by_match_id(item.match_id)
            if is_exist is not None:
                self.logger.info(f"Playclock already exists: {is_exist}")
                return is_exist
        result = await super().create(item)
        return result  # type: ignore

    async def _stop_playclock_internal(self, playclock_id: int) -> None:
        """Handle playclock stop when it reaches 0"""
        self.logger.debug(f"Stopping playclock {playclock_id} (reached 0)")
        clock_orchestrator.unregister_playclock(playclock_id)
        await self.clock_manager.end_clock(playclock_id)
        await self.update(
            playclock_id,
            PlayClockSchemaUpdate(
                playclock_status="stopping",
                playclock=0,
            ),
        )
        await asyncio.sleep(2)
        await self.update(
            playclock_id,
            PlayClockSchemaUpdate(
                playclock=None,
                playclock_status="stopped",
            ),
        )

    async def stop_playclock(self, playclock_id: int) -> None:
        """Manually stop playclock and unregister from orchestrator"""
        self.logger.debug(f"Manually stopping playclock {playclock_id}")
        state_machine = self.clock_manager.get_clock_state_machine(playclock_id)
        if state_machine:
            state_machine.stop()
        clock_orchestrator.unregister_playclock(playclock_id)
        await self.clock_manager.end_clock(playclock_id)

    async def enable_match_data_clock_queues(
        self,
        item_id: int,
        initial_value: int | None = None,
    ) -> asyncio.Queue:
        self.logger.debug(f"Enable matchdata playclock queues match id:{item_id}")
        playclock = await self.get_by_id(item_id)

        if not playclock:
            self.logger.warning(f"Playclock not found: {item_id}")

        active_clock_matches = self.clock_manager.active_playclock_matches

        if item_id not in active_clock_matches:
            self.logger.debug(f"Playclock not in active playclock matches: {item_id}")
            if initial_value is None:
                initial_value = playclock.playclock if playclock and playclock.playclock else 0
            await self.clock_manager.start_clock(
                item_id, initial_value if initial_value is not None else 0
            )

            state_machine = self.clock_manager.get_clock_state_machine(item_id)
            if state_machine and playclock and playclock.playclock_status == "running":
                state_machine.start()
            elif initial_value is not None and state_machine:
                state_machine.start()

            if state_machine and state_machine.status == "running":
                clock_orchestrator.register_playclock(item_id, state_machine)

            self.logger.debug(f"Playclock added to active playclock matches: {item_id}")
        match_queue = active_clock_matches[item_id]
        if playclock:
            await match_queue.put(playclock)
        self.logger.info(f"Playclock enabled successfully {playclock}")
        return match_queue

    @handle_service_exceptions(item_name=ITEM, operation="updating")
    async def update(
        self,
        item_id: int,
        item: PlayClockSchemaUpdate,
        **kwargs,
    ) -> PlayClockDB:
        self.logger.debug(f"Update playclock id:{item_id} data: {item}")
        async with self.db.async_session() as session:
            result = await session.execute(select(PlayClockDB).where(PlayClockDB.id == item_id))
            updated_item = result.scalars().one_or_none()

            if not updated_item:
                self.logger.warning(f"PlayClock not found: {item_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"PlayClock with id {item_id} not found",
                )

            update_data = item.model_dump(exclude_unset=True)
            update_data["version"] = (updated_item.version or 0) + 1

            for key, value in update_data.items():
                if value is not None:
                    setattr(updated_item, key, value)

            await session.flush()
            await session.commit()
            await session.refresh(updated_item)

            self.logger.debug(f"Updated playclock: {updated_item}")
            await self.trigger_update_playclock(item_id)

            return updated_item

    @handle_service_exceptions(item_name=ITEM, operation="updating")
    async def update_with_none(
        self,
        item_id: int,
        item: PlayClockSchemaUpdate,
        **kwargs,
    ) -> PlayClockDB:
        self.logger.debug(f"Update playclock with None allowed id:{item_id} data: {item}")
        async with self.db.async_session() as session:
            result = await session.execute(select(PlayClockDB).where(PlayClockDB.id == item_id))
            updated_item = result.scalars().one_or_none()

            if not updated_item:
                self.logger.warning(f"PlayClock not found: {item_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"PlayClock with id {item_id} not found",
                )

            update_data = item.model_dump(exclude_unset=True)
            update_data["version"] = (updated_item.version or 0) + 1

            for key, value in update_data.items():
                if key != "match_id" or value is not None:
                    setattr(updated_item, key, value)

            await session.flush()
            await session.commit()
            await session.refresh(updated_item)

            self.logger.debug(f"Updated playclock: {updated_item}")
            await self.trigger_update_playclock(item_id)

            return updated_item

    async def get_playclock_status(
        self,
        item_id: int,
    ) -> str | None:
        self.logger.debug(f"Get playclock status for item id:{item_id}")
        playclock: PlayClockDB | None = await self.get_by_id(item_id)
        if playclock:
            self.logger.debug(f"Playclock status: {playclock}")
            return playclock.playclock_status
        else:
            self.logger.warning(f"Playclock not found: {item_id}")
            return None

    async def get_playclock_by_match_id(self, match_id: int) -> PlayClockDB | None:
        async with self.db.async_session() as session:
            self.logger.debug(f"Get playclock by match id:{match_id}")
            result = await session.scalars(
                select(PlayClockDB).where(PlayClockDB.match_id == match_id)
            )
            if result:
                self.logger.debug(f"Playclock in DB: {result}")
                playclock: PlayClockDB | None = result.one_or_none()
                if playclock:
                    state_machine = self.clock_manager.get_clock_state_machine(playclock.id)
                    if state_machine and state_machine.status == "running":
                        playclock.playclock = state_machine.get_current_value()
                    self.logger.debug(f"Playclock found: {playclock}")
                    return playclock
        return None

    async def decrement_playclock_one_second(
        self,
        item_id: int,
    ) -> int:
        self.logger.debug(f"Decrementing playclock on one second for playclock id: {item_id}")
        result = await self.get_by_id(item_id)
        if result:
            updated_playclock = result.playclock

            if updated_playclock and updated_playclock > 0:
                updated_playclock -= 1
                return updated_playclock

            else:
                self.logger.debug("Playclock is 0, stopping")
                await self.update(
                    item_id,
                    PlayClockSchemaUpdate(
                        playclock_status="stopped",
                    ),
                )
                return 0
        else:
            self.logger.warning(f"Playclock not found: {item_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Playclock id:{item_id} not found",
            )

    async def trigger_update_playclock(
        self,
        playclock_id: int,
    ) -> None:
        self.logger.debug(f"Trigger update playclock for playclock id:{playclock_id}")
        playclock: PlayClockDB | None = await self.get_by_id(playclock_id)

        active_clock_matches = self.clock_manager.active_playclock_matches

        if playclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[playclock_id]
            await matchdata_clock_queue.put(playclock)
        else:
            self.logger.warning(f"No active playclock found with id:{playclock_id}")
