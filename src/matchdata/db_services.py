import asyncio
import json
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.core.models import db, BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate

update_queue = asyncio.Queue()


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDataDB)

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
                    game_clock_task=matchdata.game_clock_task,
                    paused_time=matchdata.paused_time,
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
                    f"for match id({matchdata})"
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

    async def get_gameclock_status(
        self,
        item_id: int,
    ):
        gameclock = await self.get_by_id(item_id)
        if gameclock:
            return gameclock.gameclock_status
        else:
            return None

    async def update_gameclock_status(
        self,
        item_id: int,
        new_status: str,
    ):
        updated = await self.update(
            item_id,
            MatchDataSchemaUpdate(gameclock_status=new_status),
        )

        await self.trigger_update_match_data(item_id)

        return updated

    async def decrement_gameclock(
        self,
        item_id: int,
    ):
        gameclock_status = await self.get_gameclock_status(item_id)

        while gameclock_status == "running":
            await asyncio.sleep(1)
            updated_gameclock = await asyncio.create_task(
                self.decrement_gameclock_one_second(item_id)
            )
            gameclock = await self.update_match_data(
                item_id,
                MatchDataSchemaUpdate(gameclock=updated_gameclock),
            )
            print(gameclock)
            gameclock_status = await self.get_gameclock_status(item_id)

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
                return updated_gameclock
        else:
            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

    async def event_generator_match_data(self):
        while True:
            # Wait for an item to be put into the queue
            data = await update_queue.get()

            # Convert datetime to string
            # Generate the data you want to send to the client
            json_data = json.dumps(
                {"match_data": data["match_data"]},
                default=self.default_serializer,
            )
            yield f"data: {json_data}\n\n"

    async def trigger_update_match_data(
        self,
        match_data_id: int,
    ):
        # Put the updated data into the queue
        match_data = await self.get_by_id(match_data_id)
        await update_queue.put(
            {
                # "teams_data": teams_data,
                "match_data": self.to_dict(match_data),
                # "scoreboard_data": scoreboard_data,
            }
        )

    # @staticmethod
    # def default_serializer(obj):
    #     if isinstance(obj, datetime):
    #         return obj.isoformat()
    #     raise TypeError(f"Type {type(obj)} not serializable")
    #
    # @staticmethod
    # def to_dict(model):
    #     data = {
    #         column.name: getattr(model, column.name)
    #         for column in model.__table__.columns
    #     }
    #     # Exclude the _sa_instance_state key
    #     data.pop("_sa_instance_state", None)
    #     return data


async def get_match_result_db() -> MatchDataServiceDB:
    yield MatchDataServiceDB(db)


async def async_main() -> None:
    match_service = MatchDataServiceDB(db)
    # t = await team_service.get_team_by_id(1)
    # t = await team_service.find_team_tournament_relation(6, 2)
    # print(t)
    # t = await team_service.get_team_by_eesl_id(1)
    # if t:
    #     print(t.__dict__)


if __name__ == "__main__":
    asyncio.run(async_main())
