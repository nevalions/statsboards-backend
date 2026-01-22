import asyncio
import logging
import time

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from websockets import ConnectionClosedError, ConnectionClosedOK

from ..logging_config import get_logger
from ..utils.websocket.websocket_manager import connection_manager, ws_manager

websocket_logger = logging.getLogger("backend_logger_MatchDataWebSocketManager")
connection_socket_logger = logging.getLogger("backend_logger_ConnectionManager")


class MatchWebSocketHandler:
    def __init__(self, cache_service=None):
        self.cache_service = cache_service
        self.logger = get_logger("backend_logger_MatchWebSocketHandler", self)
        self.logger.debug("Initialized MatchWebSocketHandler")

    async def send_initial_data(self, websocket: WebSocket, client_id: str, match_id: int):
        from src.helpers.fetch_helpers import (
            fetch_gameclock,
            fetch_playclock,
            fetch_with_scoreboard_data,
        )

        initial_data = await fetch_with_scoreboard_data(match_id, cache_service=self.cache_service)
        initial_data["type"] = "message-update"
        websocket_logger.debug("WebSocket Connection initial_data for type: message-update")
        websocket_logger.info(f"WebSocket Connection initial_data: {initial_data}")

        initial_playclock_data = await fetch_playclock(match_id, cache_service=self.cache_service)
        initial_playclock_data["type"] = "playclock-update"
        websocket_logger.debug("WebSocket Connection initial_data for type: playclock-update")
        websocket_logger.info(f"WebSocket Connection initial_data: {initial_playclock_data}")

        initial_gameclock_data = await fetch_gameclock(match_id, cache_service=self.cache_service)
        initial_gameclock_data["type"] = "gameclock-update"
        websocket_logger.debug("WebSocket Connection initial_data for type: gameclock-update")
        websocket_logger.info(f"WebSocket Connection initial_data: {initial_gameclock_data}")

        await websocket.send_json(initial_data)
        await websocket.send_json(initial_playclock_data)
        await websocket.send_json(initial_gameclock_data)

        if client_id in connection_manager.queues:
            await connection_manager.queues[client_id].put(initial_data)
            await connection_manager.queues[client_id].put(initial_playclock_data)
            await connection_manager.queues[client_id].put(initial_gameclock_data)
            websocket_logger.debug(
                f"Put initial_data into queue for client_id:{client_id}: {initial_data}"
            )
            websocket_logger.debug(
                f"Put initial_playclock_data into queue for client_id:{client_id}: {initial_playclock_data}"
            )
            websocket_logger.debug(
                f"Put initial_gameclock_data into queue for client_id:{client_id}: {initial_gameclock_data}"
            )
        else:
            websocket_logger.warning(
                f"No queue found for client_id {client_id}. Data not enqueued."
            )

    async def cleanup_websocket(self, client_id: str):
        await asyncio.sleep(0.1)
        await connection_manager.disconnect(client_id)
        connection_socket_logger.warning(
            f"Client {client_id} disconnected, closing connection and removing from subscriptions"
        )
        await ws_manager.disconnect(client_id)
        websocket_logger.warning(
            f"Client {client_id} disconnected from websocket, closing connection"
        )
        await ws_manager.shutdown()

    async def receive_messages(self, websocket: WebSocket, client_id: str):
        async for message in websocket.iter_json():
            message_type = message.get("type")
            if message_type == "pong":
                connection_manager.update_client_activity(client_id)
                websocket_logger.debug(f"Received pong from client {client_id}")
            else:
                websocket_logger.debug(f"Received non-pong message: {message_type}")

    async def process_data_websocket(self, websocket: WebSocket, client_id: str, match_id: int):
        websocket_logger.debug(f"WebSocketState: {websocket.application_state}")
        handlers = {
            "message-update": self.process_match_data,
            "match-update": self.process_match_data,
            "gameclock-update": self.process_gameclock_data,
            "playclock-update": self.process_playclock_data,
            "event-update": self.process_event_data,
            "matchdata": self.process_match_data,
            "gameclock": self.process_gameclock_data,
            "playclock": self.process_playclock_data,
            "match": self.process_match_data,
            "scoreboard": self.process_match_data,
        }

        while True:
            if websocket.application_state != WebSocketState.CONNECTED:
                websocket_logger.warning(
                    f"WebSocket disconnected (state: {websocket.application_state}), ending processing loop"
                )
                break

            try:
                queue = await connection_manager.get_queue_for_client(client_id)
                timeout_ = 60.0

                try:
                    data = await asyncio.wait_for(queue.get(), timeout=timeout_)

                    if not isinstance(data, dict):
                        websocket_logger.warning(f"Received non-dictionary data: {data}")
                        continue

                    message_type = data.get("type")
                    if message_type not in handlers:
                        websocket_logger.warning(f"Unknown message type received: {message_type}")
                        continue

                    if websocket.application_state == WebSocketState.CONNECTED:
                        await handlers[message_type](websocket, match_id, data)
                    else:
                        websocket_logger.warning(
                            "WebSocket disconnected, stopping message processing"
                        )
                        break

                except asyncio.TimeoutError:
                    websocket_logger.debug(f"Queue get operation timed out after {timeout_} seconds")
                    break

            except Exception as e:
                websocket_logger.error(f"Error in processing loop: {e}", exc_info=True)
                break

    async def process_match_data(self, websocket: WebSocket, match_id: int, data: dict | None = None):
        from src.helpers.fetch_helpers import fetch_with_scoreboard_data

        try:
            if websocket.application_state != WebSocketState.CONNECTED:
                websocket_logger.warning("WebSocket not connected, skipping data send")
                return

            if data is None:
                full_match_data = await fetch_with_scoreboard_data(
                    match_id, cache_service=self.cache_service
                )
                full_match_data["type"] = "match-update"
            else:
                full_match_data = data

            if websocket.application_state == WebSocketState.CONNECTED:
                websocket_logger.debug(f"Processing match data type: {full_match_data['type']}")
                websocket_logger.debug(f"Match data fetched: {full_match_data}")
                try:
                    await websocket.send_json(full_match_data)
                except ConnectionClosedOK:
                    websocket_logger.debug("WebSocket closed normally while sending data")
                except ConnectionClosedError as e:
                    websocket_logger.error(f"WebSocket closed with error while sending data: {e}")
            else:
                websocket_logger.warning(
                    f"WebSocket no longer connected (state: {websocket.application_state}), skipping data send"
                )

        except Exception as e:
            websocket_logger.error(f"Error processing match data: {e}", exc_info=True)

    async def process_gameclock_data(self, websocket: WebSocket, match_id: int, data: dict | None = None):
        try:
            if websocket.application_state != WebSocketState.CONNECTED:
                websocket_logger.warning("WebSocket not connected, skipping gameclock data send")
                return

            if data is None or "data" not in data:
                from src.helpers.fetch_helpers import fetch_gameclock

                gameclock_data = await fetch_gameclock(match_id, cache_service=self.cache_service)
                gameclock_data["type"] = "gameclock-update"
            else:
                gameclock_data = {
                    "match_id": match_id,
                    "gameclock": data.get("data"),
                    "type": "gameclock-update"
                }

            if websocket.application_state == WebSocketState.CONNECTED:
                websocket_logger.debug(f"Processing match data type: {gameclock_data['type']}")
                websocket_logger.debug(f"Gameclock data fetched: {gameclock_data}")
                try:
                    await websocket.send_json(gameclock_data)
                except ConnectionClosedOK:
                    websocket_logger.debug("WebSocket closed normally while sending gameclock data")
                except ConnectionClosedError as e:
                    websocket_logger.error(
                        f"WebSocket closed with error while sending gameclock data: {e}"
                    )
            else:
                websocket_logger.warning(
                    f"WebSocket no longer connected (state: {websocket.application_state}), skipping gameclock data send"
                )
        except Exception as e:
            websocket_logger.error(f"Error processing gameclock data: {e}", exc_info=True)

    async def process_playclock_data(self, websocket: WebSocket, match_id: int, data: dict | None = None):
        try:
            if websocket.application_state != WebSocketState.CONNECTED:
                websocket_logger.warning("WebSocket not connected, skipping playclock data send")
                return

            if data is None or "data" not in data:
                from src.helpers.fetch_helpers import fetch_playclock

                playclock_data = await fetch_playclock(match_id, cache_service=self.cache_service)
                playclock_data["type"] = "playclock-update"
            else:
                playclock_data = {
                    "match_id": match_id,
                    "playclock": data.get("data"),
                    "type": "playclock-update"
                }

            if websocket.application_state == WebSocketState.CONNECTED:
                websocket_logger.debug(f"Processing match data type: {playclock_data['type']}")
                websocket_logger.debug(f"Playclock data fetched: {playclock_data}")
                try:
                    await websocket.send_json(playclock_data)
                except ConnectionClosedOK:
                    websocket_logger.debug("WebSocket closed normally while sending playclock data")
                except ConnectionClosedError as e:
                    websocket_logger.error(
                        f"WebSocket closed with error while sending playclock data: {e}"
                    )
            else:
                websocket_logger.warning(
                    f"WebSocket no longer connected (state: {websocket.application_state}), skipping playclock data send"
                )
        except Exception as e:
            websocket_logger.error(f"Error processing playclock data: {e}", exc_info=True)

    async def process_event_data(self, websocket: WebSocket, match_id: int, data: dict | None = None):
        try:
            if websocket.application_state != WebSocketState.CONNECTED:
                self.logger.debug("WebSocket not connected, skipping event data send")
                return

            if data is None:
                from src.helpers.fetch_helpers import fetch_event

                event_data = await fetch_event(match_id, cache_service=self.cache_service)
                event_data["type"] = "event-update"
            else:
                event_data = data

            if websocket.application_state == WebSocketState.CONNECTED:
                websocket_logger.debug(f"Processing match data type: {event_data['type']}")
                websocket_logger.debug(f"Event data fetched: {event_data}")
                try:
                    await websocket.send_json(event_data)
                except ConnectionClosedOK:
                    websocket_logger.debug("WebSocket closed normally while sending event data")
                except ConnectionClosedError as e:
                    websocket_logger.error(
                        f"WebSocket closed with error while sending event data: {e}"
                    )
            else:
                websocket_logger.warning(
                    f"WebSocket no longer connected (state: {websocket.application_state}), skipping event data send"
                )
        except Exception as e:
            websocket_logger.error(f"Error processing event data: {e}", exc_info=True)

    async def handle_websocket_connection(
        self, websocket: WebSocket, client_id: str, match_id: int
    ):
        websocket_logger.debug(f"Websocket endpoint /ws/id/{match_id}/{client_id} {websocket} ")

        extensions = websocket.headers.get("sec-websocket-extensions", "")
        compression_enabled = "permessage-deflate" in extensions
        websocket_logger.info(
            f"WebSocket connection from client {client_id} for match {match_id}: "
            f"compression={compression_enabled}, extensions={extensions}"
        )

        await websocket.accept()
        await connection_manager.connect(websocket, client_id, match_id)
        await ws_manager.startup()

        async def ping_task():
            while True:
                await asyncio.sleep(30)
                try:
                    ping_message = {"type": "ping", "timestamp": time.time()}
                    await websocket.send_json(ping_message)
                    websocket_logger.debug(f"Sent ping to client {client_id}")
                except Exception as e:
                    websocket_logger.error(f"Error sending ping to client {client_id}: {e}")
                    break

        ping_handle = asyncio.create_task(ping_task())
        receive_handle = asyncio.create_task(self.receive_messages(websocket, client_id))

        try:
            await self.send_initial_data(websocket, client_id, match_id)
            await self.process_data_websocket(websocket, client_id, match_id)

        except WebSocketDisconnect as e:
            websocket_logger.error(f"WebSocket disconnect error:{str(e)}", exc_info=True)
        except ConnectionClosedOK as e:
            websocket_logger.debug(f"ConnectionClosedOK error:{str(e)}", exc_info=True)
        except asyncio.TimeoutError as e:
            websocket_logger.error(f"TimeoutError error:{str(e)}", exc_info=True)
        except RuntimeError as e:
            websocket_logger.error(f"RuntimeError error:{str(e)}", exc_info=True)
        except Exception as e:
            websocket_logger.error(f"Unexpected error:{str(e)}", exc_info=True)
        finally:
            ping_handle.cancel()
            receive_handle.cancel()
            try:
                await ping_handle
            except asyncio.CancelledError:
                pass
            try:
                await receive_handle
            except asyncio.CancelledError:
                pass
            await self.cleanup_websocket(client_id)


match_websocket_handler = MatchWebSocketHandler()
