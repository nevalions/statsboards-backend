from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import SeasonServiceDB
from .schemas import SeasonSchemaCreate, SeasonSchema, SeasonSchemaUpdate


class SeasonRouter(
    BaseRouter[
        SeasonSchema,
        SeasonSchemaCreate,
        SeasonSchemaUpdate,
    ]
):
    def __init__(self, service: SeasonServiceDB):
        super().__init__(
            "/api/seasons",
            ["seasons"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post("/", response_model=SeasonSchema)
        async def create_season(item: SeasonSchemaCreate):
            new_ = await self.service.create_season(item)
            return new_.__dict__

        @router.put("/", response_model=SeasonSchema)
        async def update_season(
                item_id: int,
                item: SeasonSchemaUpdate,
        ):
            update_ = await self.service.update_season(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail="Season not found",
                )
            return update_.__dict__

        @router.get("/year/{season_year}", response_model=SeasonSchema)
        async def get_season_by_year(season_year: int):
            season = await self.service.get_season_by_year(season_year)
            if season is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season {season_year} not found",
                )
            return season.__dict__

        @router.get("/year/{year}/tournaments")
        async def get_tournaments_by_year(year: int):
            return await self.service.get_tournaments_by_year(year)

        @router.get("/year/{year}/teams")
        async def get_teams_by_year(year: int, ):
            return await self.service.get_teams_by_year(year)

        return router


api_season_router = SeasonRouter(SeasonServiceDB(db)).route()
