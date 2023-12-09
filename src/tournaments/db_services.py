import asyncio

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import db, BaseServiceDB, TournamentDB
from .schemas import TournamentSchemaCreate, TournamentSchemaUpdate


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TournamentDB)

    async def create_tournament(self, t: TournamentSchemaCreate):
        try:
            # Try to query for existing item
            if t.tournament_eesl_id:
                print(t.tournament_eesl_id)
                tournament = await self.update_item_by_eesl_id(
                    t,
                    "tournament_eesl_id",
                    t.tournament_eesl_id,
                )
                if tournament:
                    return tournament
            else:
                tournament = self.model(
                    title=t.title,
                    description=t.description,
                    tournament_logo_url=t.tournament_logo_url,
                    season_id=t.season_id,
                    tournament_eesl_id=t.tournament_eesl_id,
                )
                return await super().create(tournament)
        except Exception as ex:
            print(ex)
            raise HTTPException(
                status_code=409,
                detail=f"Tournament eesl "
                f"id({t.tournament_eesl_id}) "
                f"returned some error",
            )

    async def get_tournament_by_eesl_id(
        self,
        value,
        field_name="tournament_eesl_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update_tournament(
        self,
        item_id: int,
        item: TournamentSchemaUpdate,
        **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )


async def get_tournament_db() -> TournamentServiceDB:
    yield TournamentServiceDB(db)


async def async_main() -> None:
    tournament_service = TournamentServiceDB(db)
    # t = await tournament_service.get_tournaments_by_year(2222)
    # print(t)
    # print(t.__dict__)


if __name__ == "__main__":
    asyncio.run(async_main())
