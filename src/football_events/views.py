from typing import List

from fastapi import (
    HTTPException,
)

from src.core import BaseRouter, db
from .db_services import FootballEventServiceDB
from .schemas import (
    FootballEventSchemaCreate,
    FootballEventSchemaUpdate,
    FootballEventSchema,
)


class FootballEventRouter(
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

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=FootballEventSchema,
        )
        async def create_football_event(football_event: FootballEventSchemaCreate):
            new_football_event = await self.service.create_match_football_event(
                football_event
            )
            return new_football_event.__dict__

        @router.put(
            "/{item_id}/",
            response_model=FootballEventSchema,
        )
        async def update_football_event_endpoint(
            item_id: int,
            football_event: FootballEventSchemaUpdate,
        ):
            football_event_update = await self.service.update_match_football_event(
                item_id,
                football_event,
            )

            if football_event_update is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match event " f"id({item_id}) " f"not found",
                )
            return football_event_update

        @router.get(
            "/match_id/{match_id}/",
            response_model=List[FootballEventSchema],
        )
        async def get_football_events_by_match_id(match_id: int):
            return await self.service.get_match_football_events_by_match_id(match_id)

        return router


api_football_event_router = FootballEventRouter(FootballEventServiceDB(db)).route()
