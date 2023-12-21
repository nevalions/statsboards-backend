import logging

import asyncio
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.core.models import db, BaseServiceDB, MatchDataDB
from src.helpers.sse_queue import MatchEventQueue
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate

# matchdata_gameclock_queue = MatchEventQueue(database=db, model=MatchDataDB)

update_queue_match_data = asyncio.Queue()
update_queue_match_data_playclock = asyncio.Queue()


# update_queue_match_data_gameclock = asyncio.Queue()


# Add the following import at the beginning of your Python file


# Inside your methods, add logging statements


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDataDB)
        self.match_event_queues = {}

    async def create_match_event_queue(self):
        matchdata_gameclock_queue = asyncio.Queue()
        return matchdata_gameclock_queue

    async def get_match_event_queue(self, match_data_id):
        return self.match_event_queues.get(match_data_id)

    async def flush_match_event_queue(self, match_data_id):
        # Remove the queue for this match
        self.match_event_queues.pop(match_data_id, None)

    async def get_active_match_ids(self):
        # Return a list of active match IDs (keys in the match_event_queues dictionary)
        return list(self.match_event_queues.keys())

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

                if match_result.game_status == "in-progress":
                    match_data_id = match_result.id

                    # Check if the queue already exists for this match
                    if match_data_id not in self.match_event_queues:
                        matchdata_gameclock_queue = (
                            await self.create_match_event_queue()
                        )
                        # Store the queue for this match
                        self.match_event_queues[
                            match_data_id
                        ] = matchdata_gameclock_queue

                    match_queue = self.match_event_queues.get(match_result.id)

                    # Check if the queue exists before putting the data
                    if match_queue:
                        await match_queue.put(
                            {"match_data": self.to_dict(match_result)}
                        )

                return match_result
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating result "
                    f"for match id({matchdata})"
                    f"returned some error",
                )

    # async def get_match_data_by_id(self, match_id: int):
    #     return await self.get_by_id(match_id)

    async def enable_match_data_events_queues(self, item_id: int):
        print(item_id)
        match_data = await self.get_by_id(item_id)
        print(match_data)

        if match_data:
            # Check if the game_status has changed to "in-progress"
            if match_data.game_status == "in-progress":
                match_data_id = match_data.id
                print(match_data.game_status)

                # Check if the queue already exists for this match
                if match_data_id not in self.match_event_queues:
                    matchdata_gameclock_queue = await self.create_match_event_queue()
                    # Store the queue for this match
                    self.match_event_queues[match_data_id] = matchdata_gameclock_queue
                    print(self.match_event_queues)

            match_queue = self.match_event_queues.get(match_data.id)

            # Check if the queue exists before putting the data
            if match_queue:
                await match_queue.put({"match_data": self.to_dict(match_data)})
                print(match_queue)
            else:
                print("Match not started")
        else:
            print(f"Match data {item_id} not found")

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

    # async def update_gameclock_status(
    #     self,
    #     item_id: int,
    #     new_status: str,
    # ):
    #     updated = await self.update(
    #         item_id,
    #         MatchDataSchemaUpdate(gameclock_status=new_status),
    #     )
    #
    #     await self.trigger_update_match_data_gameclock(item_id)
    #
    #     return updated

    async def decrement_gameclock(
        self,
        item_id: int,
    ):
        gameclock_status = await self.get_gameclock_status(item_id)

        while gameclock_status == "running":
            await asyncio.sleep(1)
            updated_gameclock = await self.decrement_gameclock_one_second(item_id)
            # print(updated_gameclock)
            gameclock = await self.update(
                item_id,
                MatchDataSchemaUpdate(gameclock=updated_gameclock),
            )

            # # Extract the relevant information for SSE
            # gameclock_data = {
            #     "gameclock": gameclock.gameclock,
            #     "gameclock_status": gameclock.gameclock_status,
            # }

            matchdata_gameclock_queue = await self.get_match_event_queue(item_id)
            # print(matchdata_gameclock_queue)

            # Send the relevant data in SSE
            await matchdata_gameclock_queue.put({"match_data": self.to_dict(gameclock)})

            gameclock_status = await self.get_gameclock_status(item_id)

        return await self.get_by_id(item_id)

    async def decrement_gameclock_one_second(
        self,
        item_id: int,
    ):
        result = await self.get_by_id(item_id)
        if result:
            updated_gameclock = result.gameclock

            if updated_gameclock and updated_gameclock >= 0:
                updated_gameclock -= 1
                return updated_gameclock

            else:
                await self.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        gameclock=0,
                        gameclock_status="stopped",
                    ),
                )
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
        # match_result = await self.get_match_data_by_id(item_id)
        # if match_result:
        #     if match_result.game_status == "in-progress":
        #         match_data_id = match_result.id
        #
        #         # Check if the queue already exists for this match
        #         if match_data_id not in self.match_event_queues:
        #             matchdata_gameclock_queue = await self.create_match_event_queue()
        #             # Store the queue for this match
        #             self.match_event_queues[match_data_id] = matchdata_gameclock_queue
        #
        #         match_queue = self.match_event_queues.get(match_result.id)
        #
        #         # Check if the queue exists before putting the data
        #         if match_queue:
        #             await match_queue.put({"match_data": self.to_dict(match_result)})
        matchdata_gameclock_queue = await self.get_match_event_queue(match_id)

        while True:
            if matchdata_gameclock_queue:
                data = await matchdata_gameclock_queue.get()
                if data:
                    json_data = json.dumps(
                        data,
                        default=self.default_serializer,
                    )
                    yield f"data: {json_data}\n\n"
                else:
                    await asyncio.sleep(0.1)
            else:
                # Log the error or take appropriate action
                print(f"Queue not found for MatchData ID:{match_id}")
                await asyncio.sleep(0.5)

    # async def event_generator_get_match_data_gameclock(self, item_id):
    #     matchdata_gameclock_queue = await self.get_match_event_queue(item_id)
    #
    #     while True:
    #         data = await matchdata_gameclock_queue.get()
    #         if data:
    #
    #         else:
    #             await asyncio.sleep(0.5)

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
        # print(matchdata_gameclock_queue)

        await matchdata_gameclock_queue.put({"match_data": self.to_dict(match_data)})

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


# async def get_match_result_db() -> MatchDataServiceDB:
#     yield MatchDataServiceDB(db)
#
#
# async def async_main() -> None:
#     match_service = MatchDataServiceDB(db)
#     # t = await team_service.get_team_by_id(1)
#     # t = await team_service.find_team_tournament_relation(6, 2)
#     # print(t)
#     # t = await team_service.get_team_by_eesl_id(1)
#     # if t:
#     #     print(t.__dict__)

#
# if __name__ == "__main__":
#     asyncio.run(async_main())
