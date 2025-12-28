import asyncio
import time

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, GameClockDB

from ..logging_config import get_logger, setup_logging
from .schemas import GameClockSchemaBase, GameClockSchemaCreate, GameClockSchemaUpdate

setup_logging()


class ClockManager:
    def __init__(self):
        self.active_gameclock_matches = {}
        self.logger = get_logger("backend_logger_ClockManager", self)
        self.logger.debug("Initialized ClockManager")

    async def start_clock(self, match_id):
        self.logger.debug("Start clock in clock manager")
        if match_id not in self.active_gameclock_matches:
            self.active_gameclock_matches[match_id] = asyncio.Queue()

    async def end_clock(self, match_id):
        self.logger.debug("Stop clock in clock manager")
        if match_id in self.active_gameclock_matches:
            del self.active_gameclock_matches[match_id]

    async def update_queue_clock(self, match_id, message):
        if match_id in self.active_gameclock_matches:
            self.logger.debug("Update clock in clock manager")
            queue = self.active_gameclock_matches[match_id]
            await queue.put(message)


class GameClockServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, GameClockDB)
        self.clock_manager = ClockManager()
        self.logger = get_logger("backend_logger_GameClockServiceDB", self)
        self.logger.debug("Initialized GameClockServiceDB")

    async def create(self, item: GameClockSchemaCreate):
        self.logger.debug(f"Create gameclock: {item}")
        async with self.db.async_session() as session:
            try:
                gameclock_result = GameClockDB(
                    gameclock=item.gameclock,
                    gameclock_max=item.gameclock_max,
                    gameclock_status=item.gameclock_status,
                    match_id=item.match_id,
                )

                self.logger.debug("Is gameclock exist")
                is_exist = await self.get_gameclock_by_match_id(item.match_id)
                if is_exist:
                    self.logger.info(f"gameclock already exists: {gameclock_result}")
                    return gameclock_result

                session.add(gameclock_result)
                await session.commit()
                await session.refresh(gameclock_result)

                self.logger.info(f"gameclock created: {gameclock_result}")
                return gameclock_result
            except Exception as ex:
                self.logger.error(
                    f"Error creating gameclock with data: {item} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail="While creating gameclock for match)returned some error",
                )

    async def enable_match_data_gameclock_queues(
        self,
        item_id: int,
    ):
        self.logger.debug(f"Enable matchdata gameclock queues match id:{item_id}")
        gameclock: GameClockSchemaBase = await self.get_by_id(item_id)

        if not gameclock:
            self.logger.warning(f"Gameclock not found: {item_id}")
            # raise ValueError(f"Gameclock {item_id} not found")

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if item_id not in active_clock_matches:
            self.logger.debug(f"Gameclock not in active gameclock matches: {item_id}")
            await self.clock_manager.start_clock(item_id)
            self.logger.debug(f"Gameclock added to active gameclock matches: {item_id}")
        match_queue = active_clock_matches[item_id]
        await match_queue.put(gameclock)
        self.logger.info(f"Gameclock enabled successfully {gameclock}")
        return match_queue

    async def update(
        self,
        item_id: int,
        item: GameClockSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update gameclock endpoint id:{item_id} data: {item}")
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        self.logger.debug(f"Updated gameclock: {updated_}")
        await self.trigger_update_gameclock(item_id)
        return updated_

    async def get_gameclock_status(
        self,
        item_id: int,
    ):
        self.logger.debug(f"Get gameclock status for item id:{item_id}")
        gameclock: GameClockSchemaBase = await self.get_by_id(item_id)
        if gameclock:
            self.logger.debug(f"Gameclock status: {gameclock}")
            return gameclock.gameclock_status
        else:
            self.logger.warning(f"Gameclock not found: {item_id}")
            return None

    async def get_gameclock_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            self.logger.debug(f"Get gameclock by match id:{match_id}")
            result = await session.scalars(
                select(GameClockDB).where(GameClockDB.match_id == match_id)
            )
            if result:
                self.logger.debug(f"Gameclock in DB: {result}")
                gameclock = result.one_or_none()
                if gameclock:
                    self.logger.debug(f"Gameclock found: {gameclock}")
                    return gameclock

    async def decrement_gameclock(
        self,
        background_tasks: BackgroundTasks,
        gameclock_id: int,
    ):
        self.logger.debug(f"Decrement gameclock by id:{gameclock_id}")

        if gameclock_id in self.clock_manager.active_gameclock_matches:
            background_tasks.add_task(
                self.loop_decrement_gameclock,
                gameclock_id,
            )
        else:
            self.logger.warning(f"Gameclock not found by id:{gameclock_id}")

    async def loop_decrement_gameclock(self, gameclock_id: int):
        self.logger.debug(f"Loop decrement gameclock by id:{gameclock_id}")
        next_time = time.monotonic()
        while True:
            next_time += 1
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            gameclock_status = await self.get_gameclock_status(gameclock_id)
            self.logger.debug(f"Gameclock status: {gameclock_status}")

            if (
                gameclock_status != "running"
            ):  # If game clock is not running, stop the loop
                break

            gameclock_obj: GameClockSchemaBase = await self.get_by_id(
                gameclock_id
            )  # Get current game clock object
            updated_gameclock = max(0, gameclock_obj.gameclock - 1)
            self.logger.debug(f"Updated gameclock: {updated_gameclock}")

            if updated_gameclock != 0:
                await self.update(
                    gameclock_id,
                    GameClockSchemaUpdate(gameclock=updated_gameclock),
                )
            else:
                self.logger.debug("Stopping gameclock")
                await self.update(
                    gameclock_id,
                    GameClockSchemaUpdate(
                        gameclock=0,
                        gameclock_status="stopped",
                    ),
                )
        self.logger.debug("Returning gameclock")
        return await self.get_by_id(gameclock_id)

    async def trigger_update_gameclock(
        self,
        gameclock_id: int,
    ):
        self.logger.debug(f"Trigger update gameclock for gameclock id:{gameclock_id}")
        gameclock: GameClockSchemaBase = await self.get_by_id(gameclock_id)

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if gameclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[gameclock_id]
            await matchdata_clock_queue.put(gameclock)
        else:
            self.logger.warning(f"No active gameclock found with id:{gameclock_id}")
