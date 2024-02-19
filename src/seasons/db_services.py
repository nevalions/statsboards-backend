import asyncio

from sqlalchemy import select, and_

from src.core.models import db, BaseServiceDB, SeasonDB, TournamentDB, SportDB, TeamDB
from .schemas import SeasonSchemaCreate, SeasonSchemaUpdate


class SeasonServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(
            database,
            model=SeasonDB,
        )

    async def create_season(self, s: SeasonSchemaCreate):
        season = self.model(
            year=s.year,
            description=s.description,
        )
        return await super().create(season)

    async def update_season(
            self,
            item_id: int,
            item: SeasonSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_season_by_year(self, season_year: int):
        async with self.db.async_session() as session:
            season = await session.execute(select(SeasonDB).filter_by(year=season_year))
            return season.scalars().one_or_none()

    async def get_tournaments_by_year(
            self,
            year: int,
            key: str = "year",
    ):
        return await self.get_related_items_level_one_by_key_and_value(
            key,
            year,
            "tournaments",
        )

    async def get_tournaments_by_year_and_sport(
            self,
            year: int,
            sport_id: int,
    ):
        async with self.db.async_session() as session:
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.year == year, SportDB.id == sport_id))
            )
            results = await session.execute(stmt)
            tournaments = results.scalars().all()
            return tournaments

    async def get_tournaments_by_season_and_sport_ids(
            self,
            season_id: int,
            sport_id: int,
    ):
        async with self.db.async_session() as session:
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.id == season_id, SportDB.id == sport_id))
            )
            results = await session.execute(stmt)
            tournaments = results.scalars().all()
            return tournaments

    async def get_teams_by_year(
            self,
            year: int,
            key: str = "year",
    ):
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="teams",
        )

    async def get_matches_by_year(
            self,
            year: int,
            key: str = "year",
    ):
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="matches",
        )


async def get_season_db() -> SeasonServiceDB:
    yield SeasonServiceDB(db)


async def async_main() -> None:
    season_service = SeasonServiceDB(db)

    # try:
    # get_season = await season_service.get_by_id(1)
    # print(get_season.__dict__)
    # get_tours = await season_service.get_tournaments_by_year(2222)
    get_tours = await season_service.get_teams_by_year(2222)
    print(get_tours)
    for tour in get_tours:
        print(tour.title)
        print(tour.id)
    # for tour in get_tours:
    #     print(tour.__dict__)
    # except Exception as ex:
    #     print(ex)

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(async_main())
