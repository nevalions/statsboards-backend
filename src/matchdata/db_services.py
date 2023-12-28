import time
import asyncio
import json

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.models import BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate


update_queue_match_data = asyncio.Queue()
# update_queue_match_data_gameclock = asyncio.Queue()
update_queue_match_data_playclock = asyncio.Queue()


class MatchDataServiceDB(BaseServiceDB):
    active_matches_gameclock = {}

    def __init__(self, database):
        super().__init__(database, MatchDataDB)

    async def start_match_gameclock(self, match_id):
        if match_id not in self.active_matches_gameclock:
            self.active_matches_gameclock[match_id] = asyncio.Queue()

    async def end_match(self, match_id):
        if match_id in self.active_matches_gameclock:
            del self.active_matches_gameclock[match_id]

    async def update_queue_match_data_gameclock(self, match_id, message):
        if match_id in self.active_matches_gameclock:
            queue = self.active_matches_gameclock[match_id]
            await queue.put(message)

    async def enable_match_data_events_queues(self, item_id: int):
        match_data = await self.get_by_id(item_id)

        if not match_data:
            raise ValueError(f"Match data {item_id} not found")

        if match_data.game_status != "in-progress":
            print(match_data.game_status)
            raise ValueError("Match not in progress")

        # Check if a queue for this match_id already exists, if not, raise an error
        if item_id not in self.active_matches_gameclock:
            self.active_matches_gameclock[item_id] = asyncio.Queue()

        match_queue = self.active_matches_gameclock[item_id]

        await match_queue.put(match_data)

        # Don't close the queue here if you want to perform more operations on it.
        return match_queue

    async def create_match_data(self, matchdata: MatchDataSchemaCreate):
        async with self.db.async_session() as session:
            try:
                match_result = MatchDataDB(
                    match_date=matchdata.match_date,
                    field_length=matchdata.field_length,
                    game_status=matchdata.game_status,
                    score_team_a=matchdata.score_team_a,
                    score_team_b=matchdata.score_team_b,
                    timeout_team_a=matchdata.timeout_team_a,
                    timeout_team_b=matchdata.timeout_team_b,
                    qtr=matchdata.qtr,
                    gameclock=matchdata.gameclock,
                    gameclock_status=matchdata.gameclock_status,
                    playclock=matchdata.playclock,
                    playclock_status=matchdata.playclock_status,
                    ball_on=matchdata.ball_on,
                    down=matchdata.down,
                    distance=matchdata.distance,
                    match_id=matchdata.match_id,
                )

                session.add(match_result)
                await session.commit()
                await session.refresh(match_result)

                return match_result
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating result "
                    f"for match id({matchdata.id})"
                    f"returned some error",
                )

    async def update_match_data(
        self,
        item_id: int,
        item: MatchDataSchemaUpdate,
        **kwargs,
    ):
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        await self.trigger_update_match_data(item_id)
        return updated_

    async def get_playclock_status(
        self,
        item_id: int,
    ):
        gameclock = await self.get_by_id(item_id)
        if gameclock:
            return gameclock.playclock_status
        else:
            return None

    async def get_gameclock_status(
        self,
        item_id: int,
    ):
        gameclock = await self.get_by_id(item_id)
        if gameclock:
            return gameclock.gameclock_status
        else:
            return None

    async def get_match_data_id_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            result = await session.scalars(
                select(MatchDataDB).where(MatchDataDB.match_id == match_id)
            )
            if result:
                print(result.__dict__)
                match_data = result.one_or_none()
                if match_data:
                    return match_data

    async def loop_decrement_gameclock(
        self,
        match_data_id,
    ):
        while True:
            start_time = time.time()
            gameclock_status = await self.get_gameclock_status(match_data_id)
            if gameclock_status != "running":
                break

            updated_gameclock = await self.decrement_gameclock_one_second(match_data_id)

            if updated_gameclock == 0:
                gameclock = await self.update(
                    match_data_id,
                    MatchDataSchemaUpdate(
                        gameclock_status="stopped",
                        gameclock=0,
                    ),
                )
            else:
                gameclock = await self.update(
                    match_data_id, MatchDataSchemaUpdate(gameclock=updated_gameclock)
                )

            await self.update_queue_match_data_gameclock(gameclock.id, gameclock)

            exec_time = time.time() - start_time
            await asyncio.sleep(max(1 - exec_time, 0))

        return await self.get_by_id(match_data_id)

    async def decrement_gameclock(
        self,
        background_tasks: BackgroundTasks,
        match_data_id: int,
    ):
        # Access the queue for the specific match directly
        if match_data_id in self.active_matches_gameclock:
            background_tasks.add_task(
                self.loop_decrement_gameclock,
                match_data_id,
            )
        else:
            print(f"No active match found with id: {match_data_id}")

    async def decrement_gameclock_one_second(
        self,
        item_id: int,
    ):
        result = await self.get_by_id(item_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

        updated_gameclock = result.gameclock or 0
        return max(updated_gameclock - 1, 0)

    async def decrement_playclock(
        self,
        item_id: int,
    ):
        playclock_status = await self.get_playclock_status(item_id)
        print(playclock_status)

        while playclock_status == "running":
            await asyncio.sleep(1)
            updated_playclock = await asyncio.create_task(
                self.decrement_playclock_one_second(item_id)
            )

            playclock = await self.update(
                item_id,
                MatchDataSchemaUpdate(playclock=updated_playclock),
            )
            await self.trigger_update_match_data_playclock(item_id)

            print(playclock)
            playclock_status = await self.get_playclock_status(item_id)

        await self.trigger_update_match_data_playclock(item_id)
        return await self.get_by_id(item_id)

    async def decrement_playclock_one_second(
        self,
        item_id: int,
    ):
        result = await self.get_by_id(item_id)
        if result:
            updated_playclock = result.playclock

            if updated_playclock and updated_playclock > 0:
                updated_playclock -= 1
                return updated_playclock

            else:
                await self.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        playclock_status="stopped",
                    ),
                )
                return 0
        else:
            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

    async def event_generator_match_data(self):
        while True:
            # Wait for an item to be put into the queue
            data = await update_queue_match_data.get()

            json_data = json.dumps(
                {"match_data": data["match_data"]},
                default=self.default_serializer,
            )
            yield f"data: {json_data}\n\n"

    async def event_generator_update_match_data_playclock(self):
        while True:
            data = await update_queue_match_data_playclock.get()

            json_data = json.dumps(
                {"match_data": data["match_data"]},
                default=self.default_serializer,
            )
            yield f"data: {json_data}\n\n"

    async def event_generator_get_match_data_gameclock(self, match_id):
        if match_id not in self.active_matches_gameclock:
            print(f"Queue not found for MatchData ID:{match_id}")
            start_game = "in-progress"
            await self.update(
                match_id,
                MatchDataSchemaUpdate(
                    game_status=start_game,
                ),
            )
            await self.enable_match_data_events_queues(match_id)

            return

        try:
            while match_id in self.active_matches_gameclock:
                print(f"Match {match_id} is active")
                message = await self.active_matches_gameclock[match_id].get()

                message_dict = self.to_dict(message)
                selected_fields_dict = {
                    field: message_dict[field]
                    for field in [
                        "gameclock",
                        "gameclock_status",
                    ]
                }

                json_data = json.dumps(
                    selected_fields_dict, default=self.default_serializer
                )

                # Check game_status from message_dict dictionary.
                if message_dict.get("game_status") == "stopped":
                    await self.end_match(match_id)
                    break

                yield f"data: {json_data}\n\n"

                # await asyncio.sleep(0.5)
            print(f"Match {match_id} stopped")
        except asyncio.CancelledError:
            pass

    async def trigger_update_match_data(
        self,
        match_data_id: int,
    ):
        # Put the updated data into the queue
        match_data = await self.get_by_id(match_data_id)
        await update_queue_match_data.put(
            {
                # "teams_data": teams_data,
                "match_data": self.to_dict(match_data),
                # "scoreboard_data": scoreboard_data,
            }
        )

    async def trigger_update_match_data_gameclock_sse(
        self,
        match_data_id: int,
    ):
        match_data = await self.get_by_id(match_data_id)

        # Access the appropriate match queue from your active_matches dictionary:
        if match_data_id in self.active_matches_gameclock:
            matchdata_gameclock_queue = self.active_matches_gameclock[match_data_id]
            await matchdata_gameclock_queue.put(match_data)

        else:
            print(f"No active match found with id: {match_data_id}")

    async def trigger_update_match_data_playclock(
        self,
        match_data_id: int,
    ):
        # Put the updated data into the queue
        match_data = await self.get_by_id(match_data_id)
        await update_queue_match_data_playclock.put(
            {
                "match_data": self.to_dict(match_data),
            }
        )
