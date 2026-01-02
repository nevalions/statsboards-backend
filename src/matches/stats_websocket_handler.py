import json
from datetime import datetime

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from src.logging_config import get_logger

from .stats_service import MatchStatsServiceDB

websocket_logger = None


class MatchStatsWebSocketHandler:
    def __init__(self, stats_service: MatchStatsServiceDB):
        self.stats_service = stats_service
        self.logger = get_logger("backend_logger_MatchStatsWebSocketHandler", self)
        self.logger.debug("Initialized MatchStatsWebSocketHandler")

        self.connected_clients: dict[int, list[tuple[WebSocket, str]]] = {}
        self.last_write_timestamps: dict[int, datetime] = {}

    async def send_initial_stats(self, websocket: WebSocket, client_id: str, match_id: int):
        try:
            stats = await self.stats_service.get_match_with_cached_stats(match_id)
            await websocket.send_json(
                {
                    "type": "full_stats_update",
                    "match_id": match_id,
                    "stats": stats,
                    "server_timestamp": datetime.now().isoformat(),
                }
            )
            self.logger.info(f"Sent initial stats to client {client_id} for match {match_id}")
        except Exception as e:
            self.logger.error(f"Error sending initial stats: {e}", exc_info=True)

    async def broadcast_stats(
        self, match_id: int, stats: dict, exclude_client_id: str | None = None
    ):
        if match_id not in self.connected_clients:
            self.logger.warning(f"No clients connected for match {match_id}")
            return

        message = {
            "type": "stats_update",
            "match_id": match_id,
            "stats": stats,
            "server_timestamp": datetime.now().isoformat(),
        }

        for websocket, client_id in self.connected_clients[match_id]:
            if exclude_client_id and client_id == exclude_client_id:
                continue

            if websocket.application_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                    self.logger.debug(f"Broadcast stats to client {client_id} for match {match_id}")
                except Exception as e:
                    self.logger.error(
                        f"Error broadcasting to client {client_id}: {e}", exc_info=True
                    )

    async def process_client_message(self, websocket: WebSocket, client_id: str, match_id: int):
        while True:
            if websocket.application_state != WebSocketState.CONNECTED:
                self.logger.warning(
                    f"WebSocket disconnected (state: {websocket.application_state}), ending message processing"
                )
                break

            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "stats_update":
                    await self.handle_stats_update(websocket, client_id, match_id, data)
                else:
                    self.logger.warning(f"Unknown message type received: {message_type}")

            except WebSocketDisconnect:
                self.logger.info(f"Client {client_id} disconnected")
                break
            except json.JSONDecodeError as e:
                self.logger.warning(f"Malformed JSON from client {client_id}: {e}")
            except Exception as e:
                self.logger.error(f"Error processing client message: {e}", exc_info=True)
                break

    async def handle_stats_update(
        self,
        websocket: WebSocket,
        client_id: str,
        match_id: int,
        data: dict,
    ):
        client_timestamp_str = data.get("timestamp")
        client_stats = data.get("stats")

        if not client_timestamp_str or not client_stats:
            self.logger.warning(f"Missing timestamp or stats in message from client {client_id}")
            return

        try:
            client_timestamp = datetime.fromisoformat(client_timestamp_str)
        except ValueError as e:
            self.logger.warning(f"Invalid timestamp format from client {client_id}: {e}")
            return

        last_timestamp = self.last_write_timestamps.get(match_id, datetime.min)

        if client_timestamp > last_timestamp:
            self.logger.info(
                f"Client {client_id} wins conflict for match {match_id} (timestamp: {client_timestamp})"
            )
            self.last_write_timestamps[match_id] = client_timestamp

            await self.broadcast_stats(match_id, client_stats, exclude_client_id=client_id)
        else:
            self.logger.info(
                f"Server wins conflict for match {match_id} (last: {last_timestamp}, client: {client_timestamp})"
            )
            current_stats = await self.stats_service.get_match_with_cached_stats(match_id)
            await websocket.send_json(
                {
                    "type": "stats_sync",
                    "match_id": match_id,
                    "stats": current_stats,
                    "server_timestamp": datetime.now().isoformat(),
                }
            )

    async def handle_websocket_connection(
        self, websocket: WebSocket, client_id: str, match_id: int
    ):
        self.logger.info(f"WebSocket connection from client {client_id} for match {match_id}")

        await websocket.accept()

        if match_id not in self.connected_clients:
            self.connected_clients[match_id] = []
        self.connected_clients[match_id].append((websocket, client_id))
        self.logger.info(
            f"Client {client_id} connected to match {match_id}. Total clients: {len(self.connected_clients[match_id])}"
        )

        try:
            await self.send_initial_stats(websocket, client_id, match_id)
            await self.process_client_message(websocket, client_id, match_id)

        except WebSocketDisconnect as e:
            self.logger.info(f"WebSocket disconnect for client {client_id}: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Unexpected error for client {client_id}: {e}", exc_info=True)
        finally:
            await self.cleanup_connection(client_id, match_id)

    async def cleanup_connection(self, client_id: str, match_id: int):
        if match_id in self.connected_clients:
            self.connected_clients[match_id] = [
                (ws, cid) for ws, cid in self.connected_clients[match_id] if cid != client_id
            ]
            self.logger.info(
                f"Removed client {client_id} from match {match_id}. Remaining clients: {len(self.connected_clients[match_id])}"
            )

            if not self.connected_clients[match_id]:
                del self.connected_clients[match_id]
                self.logger.info(f"No more clients for match {match_id}")
        else:
            self.logger.warning(f"Match {match_id} not in connected_clients during cleanup")
