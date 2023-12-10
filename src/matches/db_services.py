import asyncio

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.models import db, BaseServiceDB, MatchDB
from .shemas import MatchSchemaCreate, MatchSchemaUpdate


class MatchServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDB)

    async def create_match(self, m: MatchSchemaCreate):
        try:
            # Try to query for existing item
            if m.match_eesl_id:
                print(m.match_eesl_id)
                match = await self.update_item_by_eesl_id(
                    m,
                    "match_eesl_id",
                    m.match_eesl_id,
                )
                if match:
                    return match

            else:
                # Create new item if none exists with same eesl_id
                match = MatchDB(
                    match_eesl_id=m.match_eesl_id,
                    field_length=m.field_length,
                    match_date=m.match_date,
                    team_a_id=m.team_a_id,
                    team_b_id=m.team_b_id,
                    tournament_id=m.tournament_id,
                )

                return await super().create(match)
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Match " f"id({m.id}) " f"returned some error",
            )

    async def get_match_by_eesl_id(
            self,
            value,
            field_name="match_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_match(
            self,
            item_id: int,
            item: MatchSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )


async def get_match_db() -> MatchServiceDB:
    yield MatchServiceDB(db)


async def async_main() -> None:
    match_service = MatchServiceDB(db)
    # t = await team_service.get_team_by_id(1)
    # t = await team_service.find_team_tournament_relation(6, 2)
    # print(t)
    # t = await team_service.get_team_by_eesl_id(1)
    # if t:
    #     print(t.__dict__)


if __name__ == "__main__":
    asyncio.run(async_main())
