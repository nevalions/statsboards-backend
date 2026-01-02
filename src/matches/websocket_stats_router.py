from fastapi import APIRouter, WebSocket

from src.core import MinimalBaseRouter
from src.logging_config import get_logger

from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)
from .stats_service import MatchStatsServiceDB
from .stats_websocket_handler import MatchStatsWebSocketHandler


class MatchStatsWebSocketRouter(
    MinimalBaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(
        self,
        service: MatchServiceDB,
        stats_service: MatchStatsServiceDB,
    ):
        super().__init__(
            "/api/matches",
            ["matches-stats-websocket"],
            service,
        )
        self.stats_service = stats_service
        self.logger = get_logger("backend_logger_MatchStatsWebSocketRouter", self)
        self.stats_handler = MatchStatsWebSocketHandler(stats_service)
        self.logger.debug("Initialized MatchStatsWebSocketRouter")

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.websocket("/ws/matches/{match_id}/stats")
        async def websocket_stats_endpoint(
            websocket: WebSocket,
            match_id: int,
        ):
            client_id = f"{id(websocket)}"
            await self.stats_handler.handle_websocket_connection(websocket, client_id, match_id)

        return router
