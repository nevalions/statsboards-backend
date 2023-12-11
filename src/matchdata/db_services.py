import asyncio

from fastapi import HTTPException
from sqlalchemy import select
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
                    score_team_a=matchdata.score_team_a,
                    score_team_b=matchdata.score_team_b,
                    match_id=matchdata.match_id,
                )

                session.add(match_result)
                await session.commit()
                await session.refresh(match_result)
                return match_result
            except Exception as ex:
                print(ex)
                raise HTTPException(status_code=409,
                                    detail=f"While creating result "
                                           f"for match id({matchdata})"
                                           f"returned some error")

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

    # async def get_all_match_results(self, skip: int = 0, limit: int = 100):
    #     async with self.db.async_session() as session:
    #         stmt = select(MatchResultDB).offset(skip).limit(limit).order_by(
    #             desc(MatchResultDB.id))
    #
    #         tt = await session.execute(stmt)
    #         match_results = []
    #         for s in tt.scalars().fetchall():
    #             match_results.append(s.__dict__)
    #         return match_results

    # async def get_match_result_by_id(self, match_result_id: int):
    #     async with self.db.async_session() as session:
    #         return await session.get(MatchResultDB, match_result_id)

    # async def get_match_result_by_match_id(self, fk_match: int):
    #     async with self.db.async_session() as session:
    #         stmt = (
    #             select(MatchResultDB).where(MatchResultDB.fk_match == fk_match)
    #         )
    #         tt = await session.execute(stmt)
    #         match_results = []
    #         for s in tt.scalars().fetchall():
    #             match_results.append(s.__dict__)
    #         return match_results

    # async def delete_match_result(self, match_result_id: int):
    #     async with self.db.async_session() as session:
    #         db_match_result = await self.get_match_result_by_id(match_result_id)
    #         if db_match_result is None:
    #             raise HTTPException(status_code=404,
    #                                 detail=f"Result id({match_result_id}) not found")
    #         await session.delete(db_match_result)
    #         await session.commit()
    #         raise HTTPException(status_code=200,
    #                             detail=f"Result id({match_result_id}) for "
    #                                    f"match id({db_match_result.fk_match}) deleted")


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


if __name__ == '__main__':
    asyncio.run(async_main())
