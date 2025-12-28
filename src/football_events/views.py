from typing import List

from fastapi import (
    HTTPException,
)

from src.core import BaseRouter, db

from ..logging_config import get_logger, setup_logging
from .db_services import FootballEventServiceDB
from .schemas import (
    FootballEventSchema,
    FootballEventSchemaCreate,
    FootballEventSchemaUpdate,
)

setup_logging()
ITEM = "FOOTBALL_EVENT"


class FootballEventAPIRouter(
    BaseRouter[
        FootballEventSchema,
        FootballEventSchemaCreate,
        FootballEventSchemaUpdate,
    ]
):
    def __init__(self, service: FootballEventServiceDB):
        super().__init__(
            "/api/football_event",
            ["football_event"],
            service,
        )
        self.logger = get_logger("backend_logger_FootballEventAPIRouter", self)
        self.logger.debug("Initialized FootballEventAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=FootballEventSchema,
        )
        async def create_football_event(football_event: FootballEventSchemaCreate):
            try:
                self.logger.debug(f"Creating {ITEM} endpoint")
                new_football_event = await self.service.create_match_football_event(
                    football_event
                )
                return FootballEventSchema.model_validate(new_football_event)
            except Exception as e:
                self.logger.error(f"Error creating football_event: {e}", exc_info=e)

        @router.put(
            "/{item_id}/",
            response_model=FootballEventSchema,
        )
        async def update_football_event_endpoint(
            item_id: int,
            football_event: FootballEventSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Updating {ITEM} endpoint")
                football_event_update = await self.service.update_match_football_event(
                    item_id,
                    football_event,
                )

                if football_event_update is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Match event id({item_id}) not found",
                    )
                return football_event_update
            except Exception as e:
                self.logger.error(f"Error updating football_event: {e}", exc_info=e)

        @router.get(
            "/match_id/{match_id}/",
            response_model=List[FootballEventSchema],
        )
        async def get_football_events_by_match_id(match_id: int):
            try:
                self.logger.debug(f"Getting {ITEM} endpoint by match id:{match_id}")
                return await self.service.get_match_football_events_by_match_id(
                    match_id
                )
            except Exception as e:
                self.logger.error(
                    f"Error getting football_events_by_match_id: {e}", exc_info=e
                )

        return router


api_football_event_router = FootballEventAPIRouter(FootballEventServiceDB(db)).route()
