import asyncio
import json

from redis import asyncio as aioredis
from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, MatchDataDB
from src.helpers.sse_queue import MatchEventQueue
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate

update_queue_match_data = asyncio.Queue()
update_queue_match_data_playclock = asyncio.Queue()


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database, redis_url="redis://localhost:6379"):
        super().__init__(database, MatchDataDB)
        self.redis_url: str = redis_url

    async def create_redis_connection(self):
        try:
            redis_connection = await aioredis.from_url(
                self.redis_url, decode_responses=True
            )
            print("Successfully connected to Redis")
            return redis_connection
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            raise

    async def create_match_event_queue(self, match_data_id) -> MatchEventQueue:
        # Create a new MatchEventQueue instance each time
        redis = await self.create_redis_connection()
        return MatchEventQueue(
            redis=redis, model=MatchDataDB, match_data_id=match_data_id
        )

    async def get_match_event_queue(self, match_data_id):
        # Directly return the MatchEventQueue instance without using a dictionary
        return await self.create_match_event_queue(match_data_id)

    async def enable_match_data_events_queues(self, item_id: int):
        print(item_id)
        match_data = await self.get_by_id(item_id)
        print(match_data)

        if match_data:
            # Check if the game_status has changed to "in-progress"
            if match_data.game_status == "in-progress":
                match_data_id = match_data.id
                print(match_data.game_status)

                # Create a new MatchEventQueue instance each time
                match_queue = await self.create_match_event_queue(match_data_id)

                try:
                    await match_queue.put_redis(match_data)
                finally:
                    # Close the connection when done
                    await match_queue.close()
            else:
                print("Match not in progress")
        else:
            print(f"Match data {item_id} not found")

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

    async def decrement_gameclock(
        self,
        item_id: int,
    ):
        gameclock_status = await self.get_gameclock_status(item_id)
        matchdata_gameclock_queue = await self.get_match_event_queue(item_id)

        while gameclock_status == "running":
            await asyncio.sleep(1)
            updated_gameclock = await self.decrement_gameclock_one_second(item_id)
            # print(updated_gameclock)
            gameclock = await self.update(
                item_id,
                MatchDataSchemaUpdate(gameclock=updated_gameclock),
            )

            print(updated_gameclock)
            if updated_gameclock == 0:
                gameclock = await self.update(
                    item_id,
                    MatchDataSchemaUpdate(gameclock_status="stopped"),
                )

            await matchdata_gameclock_queue.put_redis(gameclock)
            await matchdata_gameclock_queue.publish_event(gameclock)
            gameclock_status = await self.get_gameclock_status(item_id)

        return await self.get_by_id(item_id)

    async def decrement_gameclock_one_second(
        self,
        item_id: int,
    ):
        result = await self.get_by_id(item_id)
        if result:
            updated_gameclock = result.gameclock

            if updated_gameclock and updated_gameclock > 0:
                updated_gameclock -= 1
                return updated_gameclock

            else:
                return 0
        else:
            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

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
        matchdata_gameclock_queue = await self.get_match_event_queue(match_id)

        if not matchdata_gameclock_queue:
            # Log the error or take appropriate action
            print(f"Queue not found for MatchData ID:{match_id}")
            return

        await matchdata_gameclock_queue.setup_pubsub_gameclock()
        # await matchdata_gameclock_queue.is_connection_open()

        try:
            while True or matchdata_gameclock_queue.is_connection_open() is True:
                await matchdata_gameclock_queue.is_connection_open()
                print("Connection is open")
                message = await matchdata_gameclock_queue.pubsub_gameclock.get_message(
                    ignore_subscribe_messages=True
                )
                # print(message)

                if message:
                    # Process the received data
                    data_string = message["data"]
                    data_loads = json.loads(data_string)
                    json_data = json.dumps(
                        data_loads,
                        default=self.default_serializer,
                    )
                    yield f"data: {json_data}\n\n"

                else:
                    await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # Catch CancelledError to prevent it from being propagated
            pass
        finally:
            # Close the connection when the loop is done
            await matchdata_gameclock_queue.close()

        print("Connection is closed")

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
        matchdata_gameclock_queue = await self.get_match_event_queue(match_data_id)
        await matchdata_gameclock_queue.put_redis(match_data)
        await matchdata_gameclock_queue.publish_event(match_data)

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
