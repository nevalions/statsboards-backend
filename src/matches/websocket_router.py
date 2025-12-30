from fastapi import WebSocket

from src.core import BaseRouter
from src.logging_config import get_logger, setup_logging
from ..websocket.match_handler import match_websocket_handler
from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)

setup_logging()


class MatchWebSocketRouter(
    BaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches-websocket"],
            service,
        )
        self.logger = get_logger("backend_logger_MatchWebSocketRouter", self)
        self.logger.debug("Initialized MatchWebSocketRouter")

    def route(self):
        router = super().route()

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
