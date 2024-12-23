import asyncio

from sqlalchemy import select, Result

from src.core.models import db, BaseServiceDB, SportDB
from .schemas import SportSchemaCreate, SportSchemaUpdate


class SportServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(
            database,
            model=SportDB,
        )

    async def create_sport(self, s: SportSchemaCreate):
        season = self.model(
            title=s.title,
            description=s.description,
        )
        return await super().create(season)

    async def update_sport(
        self,
        item_id: int,
        item: SportSchemaUpdate,
        **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_tournaments_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ):
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "tournaments",
        )

    async def get_teams_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ):
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "teams",
        )

    async def get_players_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ):
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "players",
        )

    async def get_positions_by_sport(
        self,
        sport_id: int,
        key: str = "id",
    ):
        return await self.get_related_item_level_one_by_key_and_value(
            key,
            sport_id,
            "positions",
        )


#
# async def get_season_db() -> SeasonServiceDB:
#     yield SeasonServiceDB(db)
#
#
# async def async_main() -> None:
#     season_service = SeasonServiceDB(db)
#
#     # try:
#     # get_season = await season_service.get_by_id(1)
#     # print(get_season.__dict__)
#     # get_tours = await season_service.get_tournaments_by_year(2222)
#     get_tours = await season_service.get_teams_by_year(2222)
#     print(get_tours)
#     for tour in get_tours:
#         print(tour.title)
#         print(tour.id)
#     # for tour in get_tours:
#     #     print(tour.__dict__)
#     # except Exception as ex:
#     #     print(ex)
#
#     await db.engine.dispose()
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
