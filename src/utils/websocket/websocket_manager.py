import asyncio
import json
import logging
from typing import Any
from collections.abc import Coroutine

import asyncpg
from starlette.websockets import WebSocket

from src.core.config import settings
from src.logging_config import get_logger
connection_socket_logger_helper = logging.getLogger("backend_logger_ConnectionManager")


class MatchDataWebSocketManager:
    def __init__(self, db_url):
        self.db_url = db_url
        self.connection = None
        self.match_data_queues = {}
        self.playclock_queues = {}
        self.gameclock_queues = {}
        self.logger = logging.getLogger("backend_logger_MatchDataWebSocketManager")
        self.logger.info("MatchDataWebSocketManager initialized")
        self.is_connected = False
        self._connection_retry_task = None

    async def maintain_connection(self):
        while True:
            try:
                if not self.is_connected:
                    await self.connect_to_db()
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(
                    f"Connection maintenance error: {str(e)}", exc_info=True
                )
                self.is_connected = False
                await asyncio.sleep(5)

    async def connect_to_db(self):
        try:
            if self.connection:
                try:
                    await self.connection.close()
                except (asyncpg.PostgresConnectionError, OSError):
                    pass

            self.connection = await asyncpg.connect(self.db_url)
            self.logger.info("Successfully connected to database")

            await self.setup_listeners()
            self.is_connected = True

        except (asyncpg.PostgresConnectionError, OSError) as e:
            self.logger.error(f"Database connection error: {str(e)}", exc_info=True)
            self.is_connected = False
            raise

    async def disconnect(self, client_id: str):
        self.logger.debug(f"Disconnecting from WebSocket with client_id: {client_id}")

        try:
            self.match_data_queues.pop(client_id)
            self.logger.info(f"Deleted match data queue for client {client_id}")
        except KeyError:
            self.logger.warning(f"No match data queue found for client {client_id}")

        try:
            self.playclock_queues.pop(client_id)
            self.logger.info(f"Deleted playclock queue for client {client_id}")
        except KeyError:
            self.logger.warning(f"No playclock queue found for client {client_id}")

        try:
            self.gameclock_queues.pop(client_id)
            self.logger.info(f"Deleted gameclock queue for client {client_id}")
        except KeyError:
            self.logger.warning(f"No gameclock queue found for client {client_id}")

    async def setup_listeners(self):
        if self.connection is None:
            raise RuntimeError("Database connection not established")

        listeners = {
            "matchdata_change": self.match_data_listener,
            "match_change": self.match_data_listener,
            "scoreboard_change": self.match_data_listener,
            "playclock_change": self.playclock_listener,
            "gameclock_change": self.gameclock_listener,
        }

        for channel, listener in listeners.items():
            try:
                await self.connection.add_listener(channel, listener)
                self.logger.info(f"Successfully added listener for channel: {channel}")
            except Exception as e:
                self.logger.error(
                    f"Error setting up listener for {channel}: {str(e)}", exc_info=True
                )
                raise

    async def startup(self):
        try:
            await self.connect_to_db()
            self._connection_retry_task = asyncio.create_task(
                self.maintain_connection()
            )
            self.logger.info("WebSocket manager startup complete")
        except Exception as e:
            self.logger.error(f"Startup error: {str(e)}", exc_info=True)
            raise

    async def _base_listener(
        self, connection, pid, channel, payload, update_type, queue_dict
    ):
        self.logger.debug(f"{update_type} notification received on channel {channel}")

        if not payload or not payload.strip():
            self.logger.warning("Empty payload received")
            return

        try:
            data = json.loads(payload.strip())
            match_id = data["match_id"]
            data["type"] = update_type

            self.logger.debug(f"Processing {update_type} for match {match_id}")

            clients = await connection_manager.get_match_subscriptions(match_id)
            for client_id in clients:
                if client_id in queue_dict:
                    await queue_dict[client_id].put(data)
                    self.logger.debug(
                        f"Added {update_type} to queue for client {client_id}"
                    )

            await connection_manager.send_to_all(data, match_id=match_id)

        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON decode error in {update_type} listener: {str(e)}", exc_info=True
            )
        except Exception as e:
            self.logger.error(
                f"Error in {update_type} listener: {str(e)}", exc_info=True
            )

    async def playclock_listener(self, connection, pid, channel, payload):
        await self._base_listener(
            connection, pid, channel, payload, "playclock-update", self.playclock_queues
        )

    async def match_data_listener(self, connection, pid, channel, payload):
        await self._base_listener(
            connection, pid, channel, payload, "match-update", self.match_data_queues
        )

    async def gameclock_listener(self, connection, pid, channel, payload):
        await self._base_listener(
            connection, pid, channel, payload, "gameclock-update", self.gameclock_queues
        )

    async def shutdown(self):
        try:
            if self._connection_retry_task:
                self._connection_retry_task.cancel()
                try:
                    await self._connection_retry_task
                except asyncio.CancelledError:
                    pass

            if self.connection:
                await self.connection.close()
                self.logger.info("Database connection closed")

            self.is_connected = False
            self.logger.info("WebSocket manager shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


ws_manager = MatchDataWebSocketManager(db_url=settings.db.db_url_websocket())


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.queues: dict[str, asyncio.Queue] = {}
        self.match_subscriptions: dict[str | int, list[str]] = {}
        self.logger = logging.getLogger("backend_logger_ConnectionManager")
        self.logger.info("ConnectionManager initialized")

    async def connect(
        self, websocket: WebSocket, client_id: str, match_id: int | None = None
    ):
        self.logger.info(f"Active Connections len: {len(self.active_connections)}")
        self.logger.info(f"Active Connections {self.active_connections}")
        self.logger.info(
            f"Connecting to WebSocket at {websocket} with client_id: {client_id} and match_id: {match_id}"
        )

        if client_id in self.active_connections:
            self.logger.debug(
                f"Client with client_id:{client_id} in active_connections: {self.active_connections}"
            )
            self.logger.warning(f"Closing connection for client_id:{client_id}")
            await self.active_connections[client_id].close()
            self.logger.debug(f"Active connections: {self.active_connections}")

        self.logger.debug(
            f"Adding new connection for client with client_id: {client_id}"
        )
        self.active_connections[client_id] = websocket
        self.queues[client_id] = asyncio.Queue()
        self.logger.info(
            f"New connection created: {self.active_connections[client_id]}"
        )
        self.logger.info(f"New queue created: {self.queues[client_id]}")

        if match_id:
            if match_id in self.match_subscriptions:
                self.logger.debug(
                    f"Match with match_id: {match_id} in match subscriptions {self.match_subscriptions}"
                )
                self.logger.debug(
                    f"Adding client with client_id: {client_id} to match_subscription {self.match_subscriptions[match_id]}"
                )
                self.match_subscriptions[match_id].append(client_id)
                self.logger.debug(
                    f"Match subscription added {self.match_subscriptions[match_id]}"
                )

            else:
                self.logger.debug(
                    f"Match with match_id: {match_id} not in match subscriptions {self.match_subscriptions}"
                )
                self.match_subscriptions[match_id] = [client_id]
                self.logger.debug(
                    f"Match subscription added {self.match_subscriptions[match_id]}"
                )

    async def cleanup_connection_resources(self, client_id: str):
        if client_id in self.queues:
            while not self.queues[client_id].empty():
                try:
                    self.queues[client_id].get_nowait()
                except asyncio.QueueEmpty:
                    break
            del self.queues[client_id]

        if client_id in self.active_connections:
            del self.active_connections[client_id]

        for _match_id, clients in self.match_subscriptions.items():
            if client_id in clients:
                clients.remove(client_id)

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            self.logger.info(
                f"Disconnecting from connections for client with client_id:{client_id}"
            )
            await self.active_connections[client_id].close()
            del self.active_connections[client_id]
            del self.queues[client_id]

            for match_id in self.match_subscriptions:
                if client_id in self.match_subscriptions[match_id]:
                    self.match_subscriptions[match_id].remove(client_id)

    async def get_active_connections(self):
        return self.active_connections

    async def get_match_subscriptions(self, match_id: int):
        return self.match_subscriptions.get(match_id, [])

    async def get_queue_for_client(self, client_id: str):
        self.logger.debug(f"Getting queue for client_id: {client_id}")
        queue = self.queues[client_id]
        return queue

    async def send_to_all(self, data: str, match_id: str | None = None):
        self.logger.debug(f"Sending data: {data} with match_id: {match_id}")
        self.logger.debug(f"Current match with match_id: {match_id}")
        if match_id:
            for client_id in self.match_subscriptions.get(match_id, []):
                if client_id in self.queues:
                    self.logger.debug(
                        f"Client with client_id: {client_id} in queues: {self.queues[client_id]}"
                    )

                    await self.queues[client_id].put(data)
                    self.logger.debug(
                        f"Data sent to all clients in queues with match id:{match_id}"
                    )

    async def send_to_match_id_channels(self, data):
        match_id = data["match_id"]
        await self.send_to_all(data, match_id=match_id)


connection_manager = ConnectionManager()


async def process_client_queue(
    client_id: str | int, handlers: dict[str | int, Coroutine[Any, Any, None]]
):
    client_id_str = str(client_id)
    if client_id_str in connection_manager.queues:
        queue = connection_manager.queues[client_id_str]
        while True:
            try:
                message = await queue.get()
                connection_socket_logger_helper.debug(
                    f"Dequeued message for client_id {client_id}: {message}"
                )

                message_type = message.get("type")

                get_handlers = handlers.get(message_type)

                if get_handlers:
                    connection_socket_logger_helper.info(
                        f"Handler executed successfully for message: {message}"
                    )
                    return get_handlers
                else:
                    connection_socket_logger_helper.warning(
                        f"No handler found for message type {message_type} in client_id {client_id}"
                    )

                queue.task_done()
            except asyncio.CancelledError:
                connection_socket_logger_helper.warning(
                    f"Queue processing canceled for client_id {client_id}"
                )
                break
            except Exception as e:
                connection_socket_logger_helper.error(
                    f"Error processing queue for client_id {client_id}: {e}"
                )
                break
