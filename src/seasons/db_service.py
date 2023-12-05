import asyncio

from sqlalchemy import select

from src.core.models import db, BaseServiceDB, SeasonDB
from .schemas import SeasonSchemaCreate, SeasonSchemaUpdate


class SeasonServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, model=SeasonDB)

    async def create_season(self, s: SeasonSchemaCreate):
        season = self.model(year=s.year, description=s.description)
        return await super().create(season)

    async def update_season(self, item_id: int, item: SeasonSchemaUpdate, **kwargs):
        return await super().update(item_id, item, **kwargs)

    async def get_season_by_year(self, season_year: int):
        async with self.db.async_session() as session:
            season = await session.execute(select(SeasonDB).filter_by(year=season_year))
            return season.scalars().one_or_none()


async def get_season_db() -> SeasonServiceDB:
    yield SeasonServiceDB(db)


async def async_main() -> None:
    season_service = SeasonServiceDB(db)

    try:
        get_season = await season_service.get_by_id(2)
        print(get_season.__dict__)
    except Exception as ex:
        print(ex)

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(async_main())
