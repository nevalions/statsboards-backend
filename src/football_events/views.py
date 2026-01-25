from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
)

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import FootballEventService
from src.core.models import FootballEventDB

from ..logging_config import get_logger
from .schemas import (
    FootballEventSchema,
    FootballEventSchemaCreate,
    FootballEventSchemaUpdate,
)

ITEM = "FOOTBALL_EVENT"


class FootballEventAPIRouter(
    BaseRouter[
        FootballEventSchema,
        FootballEventSchemaCreate,
        FootballEventSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/football_event",
            ["football_event"],
            None,
        )
        self.logger = get_logger("backend_logger_FootballEventAPIRouter", self)
        self.logger.debug("Initialized FootballEventAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=FootballEventSchema,
        )
        async def create_football_event(
            football_event_service: FootballEventService, football_event: FootballEventSchemaCreate
        ):
            try:
                self.logger.debug(f"Creating {ITEM} endpoint")
                new_football_event = await football_event_service.create(football_event)
                return FootballEventSchema.model_validate(new_football_event)
            except Exception as e:
                self.logger.error(f"Error creating football_event: {e}", exc_info=e)

        @router.put(
            "/{item_id}/",
            response_model=FootballEventSchema,
        )
        async def update_football_event_endpoint(
            football_event_service: FootballEventService,
            item_id: int,
            football_event: FootballEventSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Updating {ITEM} endpoint")
                football_event_update = await football_event_service.update(
                    item_id,
                    football_event,
                )
                if football_event_update is None:
                    raise HTTPException(status_code=404, detail=f"{ITEM} {item_id} not found")
                return football_event_update
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error updating football_event: {e}", exc_info=e)
                raise

        @router.get(
            "/match_id/{match_id}/",
            response_model=list[FootballEventSchema],
        )
        async def get_football_events_by_match_id(
            football_event_service: FootballEventService, match_id: int
        ):
            try:
                self.logger.debug(f"Getting {ITEM} endpoint by match id:{match_id}")
                return await football_event_service.get_match_football_events_by_match_id(match_id)
            except Exception as e:
                self.logger.error(f"Error getting football_events_by_match_id: {e}", exc_info=e)

        @router.get(
            "/matches/{match_id}/events-with-players/",
            summary="Get football events with embedded players",
            description="Get all football events for a match with all 17 player references pre-populated",
            responses={
                200: {"description": "Events retrieved successfully"},
                404: {"description": "Match not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def get_events_with_players(
            football_event_service: FootballEventService, match_id: int
        ):
            try:
                self.logger.debug(f"Getting {ITEM} with players endpoint for match_id:{match_id}")
                events = await football_event_service.get_events_with_players(match_id)
                if not events:
                    return {"match_id": match_id, "events": []}

                return {"match_id": match_id, "events": events}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error getting events_with_players for match {match_id}: {e}",
                    exc_info=e,
                )

        @router.delete(
            "/id/{model_id}",
            summary="Delete football event",
            description="Delete a football event by ID. Requires admin role.",
            responses={
                200: {"description": "FootballEvent deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "FootballEvent not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_football_event_endpoint(
            football_event_service: FootballEventService,
            model_id: int,
            _: Annotated[FootballEventDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete football event endpoint id:{model_id}")
            await football_event_service.delete(model_id)
            return {"detail": f"FootballEvent {model_id} deleted successfully"}

        return router


api_football_event_router = FootballEventAPIRouter().route()
