import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TeamDB
from .schemas import TeamSchemaCreate, TeamSchemaUpdate


class TeamServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TeamDB)

    async def create_or_update_team(
            self,
            t: TeamSchemaCreate | TeamSchemaUpdate,
    ):
        try:
            if t.team_eesl_id:
                team_from_db = await self.get_team_by_eesl_id(
                    t.team_eesl_id)
                if team_from_db:
                    return await self.update_team_by_eesl(
                        "team_eesl_id",
                        t,
                    )
                else:
                    return await self.create_new_team(t)
            else:
                return await self.create_new_team(t)
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Team eesl " f"id({t}) " f"returned some error",
            )

    async def update_team_by_eesl(
            self,
            eesl_field_name: str,
            t: TeamSchemaUpdate,
    ):
        return await self.update_item_by_eesl_id(
            eesl_field_name,
            t.team_eesl_id,
            t,
        )

    async def create_new_team(self, t: TeamSchemaCreate):
        team = self.model(
            team_eesl_id=t.team_eesl_id,
            title=t.title,
            description=t.description,
            team_logo_url=t.team_logo_url,
        )
        return await super().create(team)

    async def get_team_by_eesl_id(
            self,
            value,
            field_name="team_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_team(self, item_id: int, item: TeamSchemaUpdate, **kwargs):
        return await super().update(item_id, item, **kwargs)


async def get_team_db() -> TeamServiceDB:
    yield TeamServiceDB(db)


async def async_main() -> None:
    team_service = TeamServiceDB(db)
    # t = await team_service.get_team_by_id(1)
    # t = await team_service.find_team_tournament_relation(6, 2)
    # print(t)
    t = await team_service.get_team_by_eesl_id(1)
    if t:
        print(t.__dict__)


if __name__ == "__main__":
    asyncio.run(async_main())
