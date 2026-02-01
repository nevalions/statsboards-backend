from fastapi import APIRouter, WebSocket

from src.core import MinimalBaseRouter
from src.logging_config import get_logger

from ..websocket.match_handler import match_websocket_handler
from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)


class MatchWebSocketRouter(
    MinimalBaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB | None = None, service_name: str | None = None):
        super().__init__(
            "/api/matches",
            ["matches-websocket"],
            service,
            service_name=service_name,
        )
        self.logger = get_logger("MatchWebSocketRouter", self)
        self.logger.debug("Initialized MatchWebSocketRouter")

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.websocket("/ws/id/{match_id}/{client_id}/")
        async def websocket_endpoint(
            websocket: WebSocket,
            client_id: str,
            match_id: int,
        ):
            await match_websocket_handler.handle_websocket_connection(
                websocket, client_id, match_id
            )

        return router
