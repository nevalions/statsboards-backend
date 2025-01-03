import asyncio
import time

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.models import BaseServiceDB, GameClockDB
from .schemas import GameClockSchemaCreate, GameClockSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "GAMECLOCK"


class ClockManager:
    def __init__(self):
        self.active_gameclock_matches = {}
        self.logger = get_logger("backend_logger_ClockManager", self)
        self.logger.debug(f"Initialized ClockManager")

    async def start_clock(self, match_id):
        self.logger.debug(f"Clock started in Clock Manager match_id:{match_id}")
        if match_id not in self.active_gameclock_matches:
            self.active_gameclock_matches[match_id] = asyncio.Queue()

    async def end_clock(self, match_id):
        self.logger.debug(f"Clock stopped in Clock Manager match_id:{match_id}")
        if match_id in self.active_gameclock_matches:
            del self.active_gameclock_matches[match_id]

    async def update_queue_clock(self, match_id, message):
        self.logger.debug(f"Clock updated in Clock Manager match_id:{match_id}")
        if match_id in self.active_gameclock_matches:
            queue = self.active_gameclock_matches[match_id]
            await queue.put(message)


class GameClockServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, GameClockDB)
        self.clock_manager = ClockManager()
        self.logger = get_logger("backend_logger_GameClockServiceDB", self)
        self.logger.debug(f"Initialized GameClockServiceDB")

    async def create_gameclock(self, gameclock: GameClockSchemaCreate):
        async with self.db.async_session() as session:
            try:
                gameclock_result = GameClockDB(
                    gameclock=gameclock.gameclock,
                    gameclock_max=gameclock.gameclock_max,
                    gameclock_status=gameclock.gameclock_status,
                    match_id=gameclock.match_id,
                )

                is_exist = await self.get_gameclock_by_match_id(gameclock.match_id)
                if is_exist:
                    return gameclock_result

                session.add(gameclock_result)
                await session.commit()
                await session.refresh(gameclock_result)

                return gameclock_result
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating gameclock "
                    f"for match)"
                    f"returned some error",
                )

    async def enable_match_data_gameclock_queues(
        self,
        item_id: int,
    ):
        gameclock = await self.get_by_id(item_id)

        if not gameclock:
            raise ValueError(f"Gameclock {item_id} not found")

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if item_id not in active_clock_matches:
            await self.clock_manager.start_clock(item_id)
        match_queue = active_clock_matches[item_id]
        await match_queue.put(gameclock)

        return match_queue

    async def update_gameclock(
        self,
        item_id: int,
        item: GameClockSchemaUpdate,
        **kwargs,
    ):
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        await self.trigger_update_gameclock(item_id)
        print(updated_.__dict__)
        return updated_

    async def get_gameclock_status(
        self,
        item_id: int,
    ):
        gameclock = await self.get_by_id(item_id)
        if gameclock:
            return gameclock.gameclock_status
        else:
            return None

    async def get_gameclock_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            result = await session.scalars(
                select(GameClockDB).where(GameClockDB.match_id == match_id)
            )
            if result:
                print(result.__dict__)
                gameclock = result.one_or_none()
                if gameclock:
                    return gameclock

    async def loop_decrement_gameclock(self, gameclock_id: int):
        next_time = time.monotonic()
        while True:
            next_time += 1
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            gameclock_status = await self.get_gameclock_status(gameclock_id)

            if (
                gameclock_status != "running"
            ):  # If game clock is not running, stop the loop
                break

            gameclock_obj = await self.get_by_id(
                gameclock_id
            )  # Get current game clock object
            updated_gameclock = max(0, gameclock_obj.gameclock - 1)

            if updated_gameclock != 0:
                await self.update(
                    gameclock_id,
                    GameClockSchemaUpdate(gameclock=updated_gameclock),
                )
            else:
                await self.update(
                    gameclock_id,
                    GameClockSchemaUpdate(
                        gameclock=0,
                        gameclock_status="stopped",
                    ),
                )

        return await self.get_by_id(gameclock_id)

    async def decrement_gameclock(
        self,
        background_tasks: BackgroundTasks,
        gameclock_id: int,
    ):
        if gameclock_id in self.clock_manager.active_gameclock_matches:
            background_tasks.add_task(
                self.loop_decrement_gameclock,
                gameclock_id,
            )
        else:
            print(f"No active match gameclock found with id: {gameclock_id}")

    async def trigger_update_gameclock(
        self,
        gameclock_id: int,
    ):
        gameclock = await self.get_by_id(gameclock_id)

        active_clock_matches = self.clock_manager.active_gameclock_matches

        if gameclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[gameclock_id]
            await matchdata_clock_queue.put(gameclock)
        else:
            print(f"No active gameclock found with id: {gameclock_id}")
