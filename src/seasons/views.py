from typing import Annotated

from fastapi import Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import SeasonService
from src.core.models import SeasonDB, handle_view_exceptions

from ..logging_config import get_logger
from .schemas import PaginatedSeasonResponse, SeasonSchema, SeasonSchemaCreate, SeasonSchemaUpdate


class SeasonAPIRouter(
    BaseRouter[
        SeasonSchema,
        SeasonSchemaCreate,
        SeasonSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/seasons",
            ["seasons"],
            None,
        )
        self.logger = get_logger("backend_logger_SeasonAPIRouter", self)
        self.logger.debug("Initialized SeasonAPIRouter")

    def route(self):
        router = super().route()

        @router.get(
            "/",
            response_model=list[SeasonSchema],
        )
        async def get_all_seasons_endpoint(season_service: SeasonService):
            self.logger.debug("Get all seasons endpoint")
            seasons = await season_service.get_all_elements()
            return [SeasonSchema.model_validate(s) for s in seasons]

        @router.post("/", response_model=SeasonSchema)
        @handle_view_exceptions(
            error_message="Internal server error creating season",
            status_code=500,
        )
        async def create_season_endpoint(season_service: SeasonService, item: SeasonSchemaCreate):
            self.logger.debug(f"Create season endpoint got data: {item}")
            new_ = await season_service.create(item)
            if new_:
                return SeasonSchema.model_validate(new_)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Error creating new season",
                )

        @router.put("/{item_id}/", response_model=SeasonSchema)
        @handle_view_exceptions(
            error_message="Internal server error updating season",
            status_code=500,
        )
        async def update_season_endpoint(
            season_service: SeasonService,
            item_id: int,
            item: SeasonSchemaUpdate,
        ):
            self.logger.debug(f"Update season endpoint id:{item_id} data: {item}")
            update_ = await season_service.update(
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
        @handle_view_exceptions(
            error_message="Internal server error fetching season",
            status_code=500,
        )
        async def get_season_by_id_endpoint(season_service: SeasonService, item_id: int):
            self.logger.debug("Get season by id endpoint")
            item = await season_service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season with id {item_id} not found",
                )
            return self.create_response(
                item,
                f"Season ID:{item.id}",
                "text",
            )

        @router.get("/id/{item_id}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_season_id_and_sport_endpoint(
            season_service: SeasonService, item_id: int, sport_id: int
        ):
            self.logger.debug(
                f"Get tournaments by season id {item_id} sport id:{sport_id} endpoint"
            )
            return await season_service.get_tournaments_by_season_and_sport_ids(item_id, sport_id)

        @router.get("/year/{season_year}", response_model=SeasonSchema)
        @handle_view_exceptions(
            error_message="Internal server error fetching season by year",
            status_code=500,
        )
        async def season_by_year_endpoint(season_service: SeasonService, season_year: int):
            self.logger.debug(f"Get season by year {season_year} endpoint")
            season = await season_service.get_season_by_year(season_year)
            if season is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season {season_year} not found",
                )
            return SeasonSchema.model_validate(season)

        @router.get("/year/{year}/tournaments")
        async def tournaments_by_year_endpoint(season_service: SeasonService, year: int):
            self.logger.debug(f"Get tournaments by season year: {year} endpoint")
            return await season_service.get_tournaments_by_year(year)

        @router.get("/year/{year}/sports/id/{sport_id}/tournaments")
        async def tournaments_by_year_and_sport_endpoint(
            season_service: SeasonService, year: int, sport_id: int
        ):
            self.logger.debug(
                f"Get tournaments by season year: {year} and sport id:{sport_id} endpoint"
            )
            return await season_service.get_tournaments_by_year_and_sport(year, sport_id)

        @router.get("/year/{year}/teams")
        async def teams_by_year_endpoint(
            season_service: SeasonService,
            year: int,
        ):
            self.logger.debug(f"Get teams by season year: {year} endpoint")
            return await season_service.get_teams_by_year(year)

        @router.get("/year/{year}/matches")
        async def matches_by_year_endpoint(
            season_service: SeasonService,
            year: int,
        ):
            self.logger.debug(f"Get matches by season year: {year} endpoint")
            return await season_service.get_matches_by_year(year)

        @router.get(
            "/paginated",
            response_model=PaginatedSeasonResponse,
            summary="Search seasons with pagination",
            description="Search seasons by description with pagination and standard query parameters",
        )
        async def search_seasons_paginated_endpoint(
            season_service: SeasonService,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("year", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for description search"),
        ):
            self.logger.debug(
                f"Search seasons paginated: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
            )
            skip = (page - 1) * items_per_page
            response = await season_service.search_seasons_with_pagination(
                search_query=search,
                skip=skip,
                limit=items_per_page,
                order_by=order_by,
                order_by_two=order_by_two,
                ascending=ascending,
            )
            return response

        @router.delete(
            "/id/{model_id}",
            summary="Delete season",
            description="Delete a season by ID. Requires admin role.",
            responses={
                200: {"description": "Season deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Season not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_season_endpoint(
            season_service: SeasonService,
            model_id: int,
            _: Annotated[SeasonDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete season endpoint id:{model_id}")
            await season_service.delete(model_id)
            return {"detail": f"Season {model_id} deleted successfully"}

        return router


api_season_router = SeasonAPIRouter().route()
