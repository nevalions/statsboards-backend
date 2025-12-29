from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SeasonServiceDB
from .schemas import SeasonSchemaCreate, SeasonSchema, SeasonSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()


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
        self.logger = get_logger("backend_logger_SeasonAPIRouter", self)
        self.logger.debug(f"Initialized SeasonAPIRouter")

    def route(self):
        router = super().route()

        @router.post("/", response_model=SeasonSchema)
        async def create_season_endpoint(item: SeasonSchemaCreate):
            self.logger.debug(f"Create season endpoint got data: {item}")
            try:
                new_ = await self.service.create(item)
                if new_:
                    return SeasonSchema.model_validate(new_)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error creating new season",
                    )
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error creating season with data: {item} {ex}",
                    exc_info=True,
                )

        @router.put("/", response_model=SeasonSchema)
        async def update_season_endpoint(
            item_id: int,
            item: SeasonSchemaUpdate,
        ):
            self.logger.debug(f"Update season endpoint id:{item_id} data: {item}")
            update_ = await self.service.update(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail="Season not found",
                )
            return SeasonSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_season_by_id_endpoint(item_id: int):
            self.logger.debug(f"Get season by id endpoint")
            item = await self.service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season with id {item_id} not found",
                )
            return self.create_response(
                item,
                f"Season ID:{item.id}",
                "Season",
            )

        @router.get("/id/{item_id}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_season_id_and_sport_endpoint(
            item_id: int, sport_id: int
        ):
            self.logger.debug(
                f"Get tournaments by season id {item_id} sport id:{sport_id} endpoint"
            )
            return await self.service.get_tournaments_by_season_and_sport_ids(
                item_id, sport_id
            )

        @router.get("/year/{season_year}", response_model=SeasonSchema)
        async def season_by_year_endpoint(season_year: int):
            self.logger.debug(f"Get season by year {season_year} endpoint")
            season = await self.service.get_season_by_year(season_year)
            if season is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season {season_year} not found",
                )
            return SeasonSchema.model_validate(season)

        @router.get("/year/{year}/tournaments")
        async def tournaments_by_year_endpoint(year: int):
            self.logger.debug(f"Get tournaments by season year: {year} endpoint")
            return await self.service.get_tournaments_by_year(year)

        @router.get("/year/{year}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_year_and_sport_endpoint(year: int, sport_id: int):
            self.logger.debug(
                f"Get tournaments by season year: {year} and sport id:{sport_id} endpoint"
            )
            return await self.service.get_tournaments_by_year_and_sport(year, sport_id)

        @router.get("/year/{year}/teams")
        async def teams_by_year_endpoint(
            year: int,
        ):
            self.logger.debug(f"Get teams by season year: {year} endpoint")
            return await self.service.get_teams_by_year(year)

        @router.get("/year/{year}/matches")
        async def matches_by_year_endpoint(
            year: int,
        ):
            self.logger.debug(f"Get matches by season year: {year} endpoint")
            return await self.service.get_matches_by_year(year)

        return router


api_season_router = SeasonAPIRouter(SeasonServiceDB(db)).route()
