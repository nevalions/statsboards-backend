import asyncio

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.core.models import db, BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate


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
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def update_match_data_gameclock(
        self,
        item_id: int,
        gameclock: int,
    ):
        async with self.db.async_session() as session:
            # print(item_id, gameclock)
            match_data = await self.get_by_id(item_id)
            print(match_data.gameclock)
            if match_data:
                await session.execute(
                    update(MatchDataDB)
                    .where(MatchDataDB.id == item_id)
                    .values(gameclock=gameclock)
                )

                await session.commit()
                # updated_item = await self.get_by_id(item_id)
                # return updated_item
            else:
                print("Error updating gameclock")

    async def get_gameclock_status(
        self,
        item_id: int,
    ):
        async with (self.db.async_session() as session):
            stmt = select(MatchDataDB.gameclock_status).where(MatchDataDB.id == item_id)
            result = await session.execute(stmt)
            return result.scalar()

    async def update_gameclock_status(
        self,
        item_id: int,
        new_status: str,
    ):
        async with self.db.async_session() as session:
            stmt = (
                update(MatchDataDB)
                .where(MatchDataDB.id == item_id)
                .values(gameclock_status=new_status)
            )
            await session.execute(stmt)
            await session.commit()

    async def pause_gameclock(
        self,
        item_id: int,
    ):
        await self.update_gameclock_status(
            item_id,
            "paused",
        )
        status = await self.get_gameclock_status(item_id)
        print(f"Game clock status after pause: {status}")

    async def reset_gameclock(
        self,
        item_id: int,
    ):
        await self.update_gameclock_status(
            item_id,
            "stopped",
        )
        await self.update_match_data(item_id, MatchDataSchemaUpdate(gameclock=720))

    async def decrement_gameclock(
        self,
        item_id: int,
    ):
        gameclock_status = await self.get_gameclock_status(item_id)

        while gameclock_status == "running":
            await asyncio.sleep(1)
            gameclock_status = await self.get_gameclock_status(item_id)
            updated_gameclock = await asyncio.create_task(
                self.decrement_gameclock_one_second(item_id)
            )

            async with self.db.async_session() as session:
                stmt = (
                    update(MatchDataDB)
                    .where(MatchDataDB.id == item_id)
                    .values(gameclock=updated_gameclock)
                    .returning(MatchDataDB.gameclock)
                )

                result = await session.execute(stmt)
                await session.commit()
                updated_gameclock = result.scalar()
                print(updated_gameclock)

            # return updated_gameclock

    async def start_gameclock(
        self,
        item_id: int,
    ):
        await self.update_gameclock_status(
            item_id,
            "running",
        )

    async def decrement_gameclock_one_second(
        self,
        item_id: int,
    ):
        # async with self.db.async_session() as session:
        #     stmt = select(MatchDataDB).where(MatchDataDB.id == item_id)

        # result = await session.scalar(stmt)
        result = await super().get_by_id(item_id)
        updated_gameclock = result.gameclock

        if updated_gameclock:
            print(updated_gameclock)
            if updated_gameclock >= 0:
                updated_gameclock -= 1
                return updated_gameclock

            else:
                await self.update_gameclock_status(
                    item_id,
                    "stopped",
                )
                return updated_gameclock
        else:
            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )


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
