from typing import Annotated

from fastapi import Depends, HTTPException, Query

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import SportService, TeamService
from src.core.models import SportDB

from ..logging_config import get_logger
from ..teams.schemas import PaginatedTeamResponse
from .schemas import SportSchema, SportSchemaCreate, SportSchemaUpdate


class SportAPIRouter(
    BaseRouter[
        SportSchema,
        SportSchemaCreate,
        SportSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/sports",
            ["sports"],
            None,
        )
        self.logger = get_logger("backend_logger_SportAPIRouter", self)
        self.logger.debug("Initialized SportAPIRouter")

    def route(self):
        router = super().route()

        @router.get(
            "/",
            response_model=list[SportSchema],
        )
        async def get_all_sports_endpoint(sport_service: SportService):
            self.logger.debug("Get all sports endpoint")
            sports = await sport_service.get_all_elements()
            return [SportSchema.model_validate(s) for s in sports]

        @router.post(
            "/",
            response_model=SportSchema,
        )
        async def create_sport_endpoint(
            item: SportSchemaCreate,
            sport_service: SportService,
        ):
            self.logger.debug(f"Create sport endpoint got data: {item}")
            new_ = await sport_service.create(item)
            return SportSchema.model_validate(new_)

        @router.put(
            "/{item_id}/",
            response_model=SportSchema,
        )
        async def update_sport_endpoint(
            item_id: int,
            item: SportSchemaUpdate,
            sport_service: SportService,
        ):
            self.logger.debug(f"Update sport endpoint id:{item_id} data: {item}")
            update_ = await sport_service.update(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(status_code=404, detail=f"Sport {item_id} not found")
            return SportSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_model=SportSchema,
        )
        async def get_sport_by_id_endpoint(item_id: int, sport_service: SportService):
            self.logger.debug(f"Getting sport by id: {item_id} endpoint")
            item = await sport_service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sport id:{item_id} not found",
                )
            return SportSchema.model_validate(item)

        @router.get("/id/{sport_id}/tournaments")
        async def tournaments_by_sport_endpoint(sport_id: int, sport_service: SportService):
            self.logger.debug(f"Get tournaments by sport id:{sport_id} endpoint")
            return await sport_service.get_tournaments_by_sport(sport_id)

        @router.get("/id/{sport_id}/teams")
        async def teams_by_sport_endpoint(sport_id: int, sport_service: SportService):
            self.logger.debug(f"Get teams by sport id:{sport_id} endpoint")
            return await sport_service.get_teams_by_sport(sport_id)

        @router.get("/id/{sport_id}/players")
        async def players_by_sport_endpoint(sport_id: int, sport_service: SportService):
            self.logger.debug(f"Get players by sport id:{sport_id} endpoint")
            return await sport_service.get_players_by_sport(sport_id)

        @router.get("/id/{sport_id}/positions")
        async def positions_by_sport_endpoint(sport_id: int, sport_service: SportService):
            self.logger.debug(f"Get positions by sport id:{sport_id} endpoint")
            return await sport_service.get_positions_by_sport(sport_id)

        @router.get(
            "/id/{sport_id}/teams/paginated",
            response_model=PaginatedTeamResponse,
        )
        async def teams_by_sport_paginated_endpoint(
            sport_id: int,
            team_service: TeamService,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("title", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for team title"),
        ):
            self.logger.debug(
                f"Get teams by sport paginated: sport_id={sport_id}, page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
            )
            skip = (page - 1) * items_per_page
            response = await team_service.search_teams_by_sport_with_pagination(
                sport_id=sport_id,
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
            summary="Delete sport",
            description="Delete a sport by ID. Requires admin role.",
            responses={
                200: {"description": "Sport deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Sport not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_sport_endpoint(
            model_id: int,
            _: Annotated[SportDB, Depends(require_roles("admin"))],
            sport_service: SportService,
        ):
            self.logger.debug(f"Delete sport endpoint id:{model_id}")
            await sport_service.delete(model_id)
            return {"detail": f"Sport {model_id} deleted successfully"}

        return router


api_sport_router = SportAPIRouter().route()
