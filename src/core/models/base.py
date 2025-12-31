import asyncio
import json
import logging
from typing import (
    Any,
)
from collections.abc import Callable, Coroutine

import asyncpg
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
from starlette.websockets import WebSocket

from src.core.config import settings
from src.core.models.mixins import (
    CRUDMixin,
    QueryMixin,
    RelationshipMixin,
    SerializationMixin,
)
from src.logging_config import get_logger, setup_logging

setup_logging()
connection_socket_logger_helper = logging.getLogger("backend_logger_ConnectionManager")
db_logger_helper = logging.getLogger("backend_logger_base_db")

# DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{str(port)}/{db_name}"


class Database:
    def __init__(self, db_url: str, echo: bool = False):
        self.logger = get_logger("backend_logger_base_db", self)
        # self.logger.debug(f"Initializing Database with URL: {db_url}, Echo: {echo}")
        self.logger.info(f"Initializing Database with URL: {db_url}, Echo: {echo}")

        try:
            self.engine: AsyncEngine = create_async_engine(url=db_url, echo=echo)
            self.async_session: Any = async_sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Error initializing Database engine: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(
                f"Unexpected error initializing Database: {e}", exc_info=True
            )

    async def test_connection(self, test_query: str = "SELECT 1"):
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text(test_query))
                self.logger.info("Database connection successful.")
        except SQLAlchemyError as e:
            self.logger.error(
                f"SQLAlchemy error during connection test: {e}", exc_info=True
            )
            raise
        except OSError as e:
            self.logger.critical(f"OS error during connection test: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.critical(
                f"Unexpected error during database connection test: {e}", exc_info=True
            )
            raise

    async def close(self):
        await self.engine.dispose()
        self.logger.info("Database connection closed.")


db = Database(db_url=str(settings.db.db_url), echo=settings.db_echo)


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
                await asyncio.sleep(5)  # Check connection every 5 seconds
            except Exception as e:
                self.logger.error(
                    f"Connection maintenance error: {str(e)}", exc_info=True
                )
                self.is_connected = False
                await asyncio.sleep(5)  # Wait before retry

    async def connect_to_db(self):
        try:
            if self.connection:
                try:
                    await self.connection.close()
                except (asyncpg.PostgresConnectionError, OSError):
                    pass

            self.connection = await asyncpg.connect(self.db_url)
            self.logger.info("Successfully connected to database")

            # Set up notifications
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
        """Set up all database listeners"""
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
        """Initialize WebSocket manager and start connection maintenance"""
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
        """
        Base listener function that handles common notification processing logic.

        Args:
            connection: The connection object
            pid: Process ID
            channel: The notification channel
            payload: The notification payload
            update_type: Type of update (e.g., 'playclock-update', 'match-update')
            queue_dict: Dictionary of queues to use for this update type
        """
        self.logger.debug(f"{update_type} notification received on channel {channel}")

        if not payload or not payload.strip():
            self.logger.warning("Empty payload received")
            return

        try:
            data = json.loads(payload.strip())
            match_id = data["match_id"]
            data["type"] = update_type

            self.logger.debug(f"Processing {update_type} for match {match_id}")

            # Add to all relevant client queues
            clients = await connection_manager.get_match_subscriptions(match_id)
            for client_id in clients:
                if client_id in queue_dict:
                    await queue_dict[client_id].put(data)
                    self.logger.debug(
                        f"Added {update_type} to queue for client {client_id}"
                    )

            # Send to all connected clients for this match
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
        """Clean up all resources associated with a client."""
        # Clean up queue
        if client_id in self.queues:
            while not self.queues[client_id].empty():
                try:
                    self.queues[client_id].get_nowait()
                except asyncio.QueueEmpty:
                    break
            del self.queues[client_id]

        # Remove from active connections
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from match subscriptions
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
        # Return a copy of active WebSocket connections (if computation or async fetching is needed)
        return self.active_connections

    async def get_match_subscriptions(self, match_id: int):
        # Return a list of client_ids subscribed to a specific match_id
        return self.match_subscriptions.get(match_id, [])

    async def get_queue_for_client(self, client_id: str):
        self.logger.debug(f"Getting queue for client_id: {client_id}")
        # Retrieve the queue for a specific client_id asynchronously
        queue = self.queues[client_id]
        # self.logger.debug(f"Queue: {queue}")
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

                # Determine the handler based on message type
                message_type = message.get("type")
                # print(f"Message Type: {message_type}")

                # print(f"HANDLERS {handlers}")
                get_handlers = handlers.get(message_type)
                # print(f"GET_HANDLERS {get_handlers}")

                if get_handlers:
                    connection_socket_logger_helper.info(
                        f"Handler executed successfully for message: {message}"
                    )
                    return get_handlers
                    # await connection_manager.send_to_match_id_channels(data=message)
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


class BaseServiceDB(
    CRUDMixin,
    QueryMixin,
    RelationshipMixin,
    SerializationMixin,
):
    def __init__(self, database: Database, model: type):
        self.logger = get_logger("backend_logger_base_db", self)
        self.db = database
        self.model = model

    async def create_or_update(
        self,
        item_schema,
        eesl_field_name: str | None = None,
        unique_field_name: str | None = None,
        unique_field_value: Any | None = None,
        model_factory: Callable | None = None,
        **create_kwargs,
    ):
        """
        Generic create or update method for upsert operations.

        Args:
            item_schema: The schema containing the data (Create or Update schema)
            eesl_field_name: Name of the eesl_id field to use for upsert (e.g., "team_eesl_id")
            unique_field_name: Alternative unique field name for upsert (e.g., "match_id")
            unique_field_value: Value for the unique field if different from schema value
            model_factory: Optional factory function to create the model instance from schema
            **create_kwargs: Additional keyword arguments for model factory

        Returns:
            The created or updated model instance
        """
        try:
            self.logger.debug(f"Create or update {self.model.__name__}:{item_schema}")

            field_name = eesl_field_name or unique_field_name
            if not field_name:
                raise ValueError(
                    "Either eesl_field_name or unique_field_name must be provided"
                )

            field_value = unique_field_value or getattr(item_schema, field_name, None)

            if field_value:
                self.logger.debug(
                    f"Get {self.model.__name__} {field_name}:{field_value}"
                )
                existing_item = await self.get_item_by_field_value(
                    field_value, field_name
                )

                if existing_item:
                    self.logger.debug(
                        f"{self.model.__name__} {field_name}:{field_value} already exists, updating"
                    )
                    return await self._update_item(
                        existing_item, item_schema, field_name, field_value
                    )
                else:
                    self.logger.debug(f"No {self.model.__name__} in DB, create new")
                    return await self._create_item(
                        item_schema, model_factory, **create_kwargs
                    )
            else:
                self.logger.debug(f"No {field_name} in schema, create new")
                return await self._create_item(
                    item_schema, model_factory, **create_kwargs
                )
        except Exception as ex:
            self.logger.error(
                f"{self.model.__name__} returned an error: {ex}", exc_info=True
            )
            raise HTTPException(
                status_code=409,
                detail=f"{self.model.__name__} ({item_schema}) returned some error",
            )

    async def _update_item(
        self, existing_item, item_schema, field_name: str, field_value: Any
    ):
        """Internal method to update an existing item."""
        if field_name.endswith("_eesl_id"):
            return await self.update_item_by_eesl_id(
                field_name, field_value, item_schema
            )
        else:
            return await self.update(existing_item.id, item_schema)

    async def _create_item(self, item_schema, model_factory, **create_kwargs):
        """Internal method to create a new item."""
        if model_factory:
            return await self.create(model_factory(item_schema, **create_kwargs))
        else:
            schema_data = item_schema.model_dump(exclude_unset=True)
            model = self.model(**schema_data)
            return await self.create(model)


class Base(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)
