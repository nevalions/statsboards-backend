import asyncio

from fastapi import HTTPException

from src.core.models import db, BaseServiceDB, TournamentDB
from .schemas import TournamentSchemaCreate, TournamentSchemaUpdate


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, TournamentDB)

    async def create_tournament(self, t: TournamentSchemaCreate):
        try:
            # Try to query for existing item
            tournament = await self.update_item_by_eesl_id(
                t, 'tournament_eesl_id', t.tournament_eesl_id)
            if tournament:
                return tournament
            else:
                tournament = self.model(title=t.title,
                                        description=t.description,
                                        tournament_logo_url=t.tournament_logo_url,
                                        # fk_season=t.fk_season,
                                        tournament_eesl_id=t.tournament_eesl_id
                                        )
                return await super().create(tournament)
        except Exception as ex:
            print(ex)
            raise HTTPException(status_code=409,
                                detail=f"Tournament eesl "
                                       f"id({t.tournament_eesl_id}) "
                                       f"returned some error")

    async def get_tournament_by_eesl_id(self, value, field_name='tournament_eesl_id'):
        return await self.get_item_by_field_value(value=value, field_name=field_name)

    async def get_tournaments_by_year(self,
                                      year,
                                      field_name='fk_season',
                                      order_by: str = 'fk_season',
                                      descending: bool = False,
                                      skip: int = 0, limit: int = 100):
        return await self.get_items_by_attribute(value=year,
                                                 field_name=field_name,
                                                 order_by=order_by,
                                                 descending=descending,
                                                 skip=skip, limit=limit)

    async def update_tournament(self,
                                item_id: int,
                                item: TournamentSchemaUpdate, **kwargs):
        return await super().update(item_id, item, **kwargs)


async def get_tournament_db() -> TournamentServiceDB:
    yield TournamentServiceDB(db)


async def async_main() -> None:
    tournament_service = TournamentServiceDB(db)
    t = await tournament_service.get_tournament_by_eesl_id(19)
    print(t.__dict__)


if __name__ == '__main__':
    asyncio.run(async_main())
