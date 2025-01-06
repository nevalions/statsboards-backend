import time
import asyncio

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayClockDB
from .schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate, PlayClockSchemaBase
from ..logging_config import setup_logging, get_logger

setup_logging()


class ClockManager:
    def __init__(self):
        self.active_playclock_matches = {}
        self.logger = get_logger("backend_logger_ClockManager", self)
        self.logger.debug(f"Initialized ClockManager")

    async def start_clock(self, match_id):
        self.logger.debug("Start clock in clock manager")
        if match_id not in self.active_playclock_matches:
            self.active_playclock_matches[match_id] = asyncio.Queue()

    async def end_clock(self, match_id):
        if match_id in self.active_playclock_matches:
            self.logger.debug("Stop clock in clock manager")
            del self.active_playclock_matches[match_id]

    async def update_queue_clock(self, match_id, message):
        if match_id in self.active_playclock_matches:
            self.logger.debug("Update clock in clock manager")
            queue = self.active_playclock_matches[match_id]
            await queue.put(message)


class PlayClockServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, PlayClockDB)
        self.clock_manager = ClockManager()
        self.logger = get_logger("backend_logger_PlayClockServiceDB", self)
        self.logger.debug(f"Initialized PlayClockServiceDB")

    async def create_playclock(self, playclock: PlayClockSchemaCreate):
        self.logger.debug(f"Create playclock: {playclock}")
        async with self.db.async_session() as session:
            try:
                playclock_result = PlayClockDB(
                    playclock=playclock.playclock,
                    playclock_status=playclock.playclock_status,
                    match_id=playclock.match_id,
                )
                self.logger.debug(f"Is playclock exist")
                is_exist = await self.get_playclock_by_match_id(playclock.match_id)
                if is_exist:
                    self.logger.info(f"Playclock already exists: {playclock_result}")
                    return playclock_result

                session.add(playclock_result)
                await session.commit()
                await session.refresh(playclock_result)

                self.logger.info(f"Playclock created: {playclock_result}")
                return playclock_result
            except Exception as ex:
                self.logger.error(
                    f"Error creating playclock with data: {playclock} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating playclock "
                    f"for match id({playclock.match_id})"
                    f"returned some error",
                )

    async def enable_match_data_clock_queues(
        self,
        item_id: int,
    ):
        self.logger.debug(f"Enable matchdata playclock queues match id:{item_id}")
        playclock = await self.get_by_id(item_id)

        if not playclock:
            self.logger.warning(f"Playclock not found: {item_id}")
            # raise ValueError(f"Playclock {item_id} not found")

        active_clock_matches = self.clock_manager.active_playclock_matches

        if item_id not in active_clock_matches:
            self.logger.debug(f"Playclock not in active playclock matches: {item_id}")
            await self.clock_manager.start_clock(item_id)
            self.logger.debug(f"Playclock added to active playclock matches: {item_id}")
        match_queue = active_clock_matches[item_id]
        await match_queue.put(playclock)
        self.logger.info(f"Playclock enabled successfully {playclock}")
        return match_queue

    async def update_playclock(
        self,
        item_id: int,
        item: PlayClockSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update playclock id:{item_id} data: {item}")
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        self.logger.debug(f"Updated playclock: {updated_}")
        await self.trigger_update_playclock(item_id)

        return updated_

    async def get_playclock_status(
        self,
        item_id: int,
    ):
        self.logger.debug(f"Get playclock status for item id:{item_id}")
        playclock: PlayClockSchemaBase = await self.get_by_id(item_id)
        if playclock:
            self.logger.debug(f"Playclock status: {playclock}")
            return playclock.playclock_status
        else:
            self.logger.warning(f"Playclock not found: {item_id}")
            return None

    async def get_playclock_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            self.logger.debug(f"Get playclock by match id:{match_id}")
            result = await session.scalars(
                select(PlayClockDB).where(PlayClockDB.match_id == match_id)
            )
            if result:
                self.logger.debug(f"Playclock in DB: {result}")
                playclock: PlayClockSchemaBase = result.one_or_none()
                if playclock:
                    self.logger.debug(f"Playclock found: {playclock}")
                    return playclock

    async def decrement_playclock(
        self,
        background_tasks: BackgroundTasks,
        playclock_id: int,
    ):
        self.logger.debug(f"Decrement playclock by id:{playclock_id}")

        if playclock_id in self.clock_manager.active_playclock_matches:
            background_tasks.add_task(
                self.loop_decrement_playclock,
                playclock_id,
            )
        else:
            self.logger.warning(f"Playclock not found by id:{playclock_id}")

    async def loop_decrement_playclock(self, playclock_id):
        self.logger.debug(f"Loop decrement playclock by id:{playclock_id}")
        next_time = time.monotonic()
        while True:
            next_time += 1
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            # start_time = time.time()
            playclock_status = await self.get_playclock_status(playclock_id)
            self.logger.debug(f"Playclock status: {playclock_status}")
            if playclock_status != "running":
                break

            updated_playclock = await self.decrement_playclock_one_second(playclock_id)
            self.logger.debug(f"Updated playclock: {updated_playclock}")

            if updated_playclock == 0:
                self.logger.debug(f"Stopping playclock")
                await self.update(
                    playclock_id,
                    PlayClockSchemaUpdate(
                        playclock_status="stopping",
                        playclock=0,
                    ),
                )

                await asyncio.sleep(2)

                playclock: PlayClockSchemaBase = await self.update(
                    playclock_id,
                    PlayClockSchemaUpdate(
                        playclock=None,
                        playclock_status="stopped",
                    ),
                )
                self.logger.debug(f"Playclock status: {playclock.playclock_status}")

            else:
                playclock = await self.update(
                    playclock_id, PlayClockSchemaUpdate(playclock=updated_playclock)
                )

            self.logger.debug(f"Playclock updated: {playclock}")
            await self.clock_manager.update_queue_clock(
                playclock_id,
                playclock,
            )
            self.logger.debug(f"Playclock in queue updated: {playclock}")

        self.logger.debug(f"Returning playclock")
        return await self.get_by_id(playclock_id)

    async def decrement_playclock_one_second(
        self,
        item_id: int,
    ):
        self.logger.debug(
            f"Decrementing playclock on one second for playclock id: {item_id}"
        )
        result = await self.get_by_id(item_id)
        if result:
            updated_playclock = result.playclock

            if updated_playclock and updated_playclock > 0:
                updated_playclock -= 1
                return updated_playclock

            else:
                self.logger.debug(f"Playclock is 0, stopping")
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
    ):
        self.logger.debug(f"Trigger update playclock for playclock id:{playclock_id}")
        playclock: PlayClockSchemaBase = await self.get_by_id(playclock_id)

        active_clock_matches = self.clock_manager.active_playclock_matches

        if playclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[playclock_id]
            await matchdata_clock_queue.put(playclock)
        else:
            self.logger.warning(f"No active playclock found with id:{playclock_id}")
