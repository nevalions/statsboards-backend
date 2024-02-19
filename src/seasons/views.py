from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SeasonServiceDB
from .schemas import SeasonSchemaCreate, SeasonSchema, SeasonSchemaUpdate


class SeasonAPIRouter(
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
        async def create_season_endpoint(item: SeasonSchemaCreate):
            new_ = await self.service.create_season(item)
            return new_.__dict__

        @router.put("/", response_model=SeasonSchema)
        async def update_season_endpoint(
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

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_matchdata_by_id_endpoint(
                item=Depends(self.service.get_by_id),
        ):
            return self.create_response(
                item,
                f"Season ID:{item.id}",
                "Season",
            )

        @router.get("/id/{item_id}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_year_and_sport_endpoint(item_id: int, sport_id: int):
            return await (self.service.get_tournaments_by_season_and_sport_ids(item_id, sport_id))

        @router.get("/year/{season_year}", response_model=SeasonSchema)
        async def season_by_year_endpoint(season_year: int):
            season = await self.service.get_season_by_year(season_year)
            if season is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season {season_year} not found",
                )
            return season.__dict__

        @router.get("/year/{year}/tournaments")
        async def tournaments_by_year_endpoint(year: int):
            return await self.service.get_tournaments_by_year(year)

        @router.get("/year/{year}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_year_and_sport_endpoint(year: int, sport_id: int):
            return await self.service.get_tournaments_by_year_and_sport(year, sport_id)

        @router.get("/year/{year}/teams")
        async def teams_by_year_endpoint(
                year: int,
        ):
            return await self.service.get_teams_by_year(year)

        @router.get("/year/{year}/matches")
        async def matches_by_year_endpoint(
                year: int,
        ):
            return await self.service.get_matches_by_year(year)

        return router


api_season_router = SeasonAPIRouter(SeasonServiceDB(db)).route()
