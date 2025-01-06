import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    List,
    Dict,
    Coroutine,
)

import asyncpg
from fastapi import HTTPException, UploadFile
from sqlalchemy import select, update, Result, Column, TextClause, text
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    selectinload,
)
from starlette.websockets import WebSocket

from src.core.config import settings
from src.logging_config import setup_logging, get_logger

setup_logging()
connection_socket_logger_helper = logging.getLogger("backend_logger_ConnectionManager")
db_logger_helper = logging.getLogger("backend_logger_base_db")

# DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{str(port)}/{db_name}"


class Database:
    def __init__(self, db_url: str, echo: bool = False):
        self.logger = get_logger("backend_logger_base_db", self)
        self.logger.debug(f"Initializing Database with URL: ***, Echo: {echo}")
        try:
            self.engine: AsyncEngine = create_async_engine(url=db_url, echo=echo)
            self.async_session: AsyncSession | Any = async_sessionmaker(
                bind=self.engine, class_=AsyncSession, expire_on_commit=False
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Error initializing Database engine: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error initializing Database: {e}")

    async def test_connection(self, test_query: str = "SELECT 1"):
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text(test_query))
                self.logger.info("Database connection successful.")
        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error during connection test: {e}")
            raise
        except OSError as e:
            self.logger.critical(f"OS error during connection test: {e}")
            raise
        except Exception as e:
            self.logger.critical(
                f"Unexpected error during database connection test: {e}"
            )
            raise

    async def close(self):
        await self.engine.dispose()
        self.logger.info("Database connection closed.")


db = Database(db_url=settings.db.db_url, echo=settings.db_echo)


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
                except Exception:
                    pass

            self.connection = await asyncpg.connect(self.db_url)
            self.logger.info("Successfully connected to database")

            # Set up notifications
            await self.setup_listeners()
            self.is_connected = True

        except Exception as e:
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
        """Initialize the WebSocket manager and start connection maintenance"""
        try:
            await self.connect_to_db()
            self._connection_retry_task = asyncio.create_task(
                self.maintain_connection()
            )
            self.logger.info("WebSocket manager startup complete")
        except Exception as e:
            self.logger.error(f"Startup error: {str(e)}", exc_info=True)
            raise

    # async def handle_notification(self, channel, payload, update_type, queue_attr):
    #     self.logger.debug(
    #         f"{update_type.capitalize()} notification received on channel {channel}"
    #     )
    #
    #     if not payload or not payload.strip():
    #         self.logger.warning(f"Empty payload received for {update_type}")
    #         return
    #
    #     try:
    #         data = json.loads(payload.strip())
    #         match_id = data["match_id"]
    #         data["type"] = update_type
    #
    #         self.logger.info(f"Processing {update_type} update for match {match_id}")
    #
    #         # Add to all relevant client queues
    #         clients = await connection_manager.get_match_subscriptions(match_id)
    #         queues = getattr(self, queue_attr)
    #         for client_id in clients:
    #             if client_id in queues:
    #                 await queues[client_id].put(data)
    #                 self.logger.debug(
    #                     f"Added {update_type} update to queue for client {client_id}"
    #                 )
    #
    #         # Send to all connected clients for this match
    #         await connection_manager.send_to_all(data, match_id=match_id)
    #
    #     except json.JSONDecodeError as e:
    #         self.logger.error(
    #             f"JSON decode error in {update_type} listener: {str(e)}", exc_info=True
    #         )
    #     except Exception as e:
    #         self.logger.error(
    #             f"Error in {update_type} listener: {str(e)}", exc_info=True
    #         )
    #
    # async def playclock_listener(self, connection, channel, payload):
    #     await self.handle_notification(
    #         connection, channel, payload, "playclock-update", "playclock_queues"
    #     )
    #
    # async def match_data_listener(self, connection, channel, payload):
    #     await self.handle_notification(
    #         connection, channel, payload, "match-update", "match_data_queues"
    #     )
    #
    # async def gameclock_listener(self, connection, channel, payload):
    #     await self.handle_notification(
    #         connection, channel, payload, "gameclock-update", "gameclock_queues"
    #     )

    async def playclock_listener(self, connection, pid, channel, payload):
        self.logger.debug(f"Playclock notification received on channel {channel}")

        if not payload or not payload.strip():
            self.logger.warning("Empty payload received")
            return

        try:
            data = json.loads(payload.strip())
            match_id = data["match_id"]
            data["type"] = "playclock-update"

            self.logger.info(f"Processing playclock update for match {match_id}")

            # Add to all relevant client queues
            clients = await connection_manager.get_match_subscriptions(match_id)
            for client_id in clients:
                if client_id in self.playclock_queues:
                    await self.playclock_queues[client_id].put(data)
                    self.logger.debug(
                        f"Added playclock update to queue for client {client_id}"
                    )

            # Send to all connected clients for this match
            await connection_manager.send_to_all(data, match_id=match_id)

        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON decode error in playclock listener: {str(e)}", exc_info=True
            )
        except Exception as e:
            self.logger.error(f"Error in playclock listener: {str(e)}", exc_info=True)

    async def match_data_listener(self, connection, pid, channel, payload):
        self.logger.debug(f"Match data notification received on channel {channel}")

        if not payload or not payload.strip():
            self.logger.warning("Empty payload received")
            return

        try:
            data = json.loads(payload.strip())
            match_id = data["match_id"]
            data["type"] = "match-update"

            self.logger.info(f"Processing match update for match {match_id}")

            # Add to all relevant client queues
            clients = await connection_manager.get_match_subscriptions(match_id)
            self.logger.debug(f"Client ids: {clients}")
            self.logger.debug(f"Match data queues: {self.match_data_queues}")
            for client_id in clients:
                if client_id in self.match_data_queues:
                    await self.match_data_queues[client_id].put(data)
                    self.logger.debug(
                        f"Added match update to queue for client {client_id}"
                    )

            # Send to all connected clients for this match
            await connection_manager.send_to_all(data, match_id=match_id)

        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON decode error in match data listener: {str(e)}", exc_info=True
            )
        except Exception as e:
            self.logger.error(f"Error in match data listener: {str(e)}", exc_info=True)

    async def gameclock_listener(self, connection, pid, channel, payload):
        self.logger.debug(f"Gameclock notification received on channel {channel}")

        if not payload or not payload.strip():
            self.logger.warning("Empty payload received")
            return

        try:
            data = json.loads(payload.strip())
            match_id = data["match_id"]
            data["type"] = "gameclock-update"

            self.logger.info(f"Processing gameclock update for match {match_id}")

            # Add to all relevant client queues
            clients = await connection_manager.get_match_subscriptions(match_id)
            for client_id in clients:
                if client_id in self.gameclock_queues:
                    await self.gameclock_queues[client_id].put(data)
                    self.logger.debug(
                        f"Added gameclock update to queue for client {client_id}"
                    )

            # Send to all connected clients for this match
            await connection_manager.send_to_all(data, match_id=match_id)

        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON decode error in gameclock listener: {str(e)}", exc_info=True
            )
        except Exception as e:
            self.logger.error(f"Error in gameclock listener: {str(e)}", exc_info=True)

    async def shutdown(self):
        """Properly shutdown the WebSocket manager"""
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
        self.active_connections: Dict[str, WebSocket] = {}
        self.queues: Dict[str, asyncio.Queue] = {}
        self.match_subscriptions: Dict[str | int, List[str]] = {}
        self.logger = logging.getLogger("backend_logger_ConnectionManager")
        self.logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, client_id: str, match_id: int = None):
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
        # Return the list of client_ids subscribed to a specific match_id
        return self.match_subscriptions.get(match_id, [])

    async def get_queue_for_client(self, client_id: str):
        self.logger.debug(f"Getting queue for client_id: {client_id}")
        # Retrieve the queue for a specific client_id asynchronously
        queue = self.queues[client_id]
        # self.logger.debug(f"Queue: {queue}")
        return queue

    async def send_to_all(self, data: str, match_id: str = None):
        self.logger.debug(f"Sending data: {data} with match_id: {match_id}")
        self.logger.debug(
            f"Current match with match_id: {match_id}, subscriptions: {self.match_subscriptions[match_id]}"
        )
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
    client_id: str | int, handlers: Dict[str | int, Coroutine[Any, Any, None]]
):
    if client_id in connection_manager.queues:
        queue = connection_manager.queues[client_id]
        while True:
            try:
                message = await queue.get()
                connection_socket_logger_helper.debug(
                    f"Dequeued message for client_id {client_id}: {message}"
                )

                # Determine the handler based on the message type
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


class BaseServiceDB:
    def __init__(self, database: Database, model: type):
        self.logger = get_logger("backend_logger_base_db", self)
        self.db = database
        self.model = model

    async def create(self, item):
        async with self.db.async_session() as session:
            self.logger.debug(
                f"Starting to create {self.model.__name__} with data: {item.__dict__}"
            )
            try:
                session.add(item)
                await session.commit()
                await session.refresh(item)
                self.logger.info(
                    f"{self.model.__name__} created successfully: {item.__dict__}"
                )
                return item
            except Exception as ex:
                self.logger.error(
                    f"Error creating {self.model.__name__}: {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"Error creating {self.model.__name__} Check input data. {item}",
                )

    async def get_all_elements(self):
        async with self.db.async_session() as session:
            stmt = select(self.model)

            items = await session.execute(stmt)
            result = items.scalars().all()
            self.logger.debug(
                f"Fetched {len(result)} elements for {self.model.__name__}"
            )
            return list(result)

    async def get_by_id(self, item_id: int):
        self.logger.debug(
            f"Starting to fetch element with ID: {item_id} for {self.model.__name__}"
        )
        try:
            async with self.db.async_session() as session:
                # self.logger.debug(f"self model id: {self.model.id} item id:{item_id}")
                result = await session.execute(
                    select(self.model).where(self.model.id == item_id)
                )
                if result:
                    final_result = result.scalars().one_or_none()
                    self.logger.debug(f"Result found: {final_result}")
                    self.logger.debug(
                        f"Fetched element successfully with ID {item_id} for {self.model.__name__}"
                    )
                    return final_result

                else:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for {self.model.__name__}"
                    )
                    return None
        except Exception as ex:
            self.logger.error(
                f"Error fetching element with ID: {item_id} for {self.model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch element for model id:{item_id} {self.model.__name__}.",
            )

    async def get_by_id_and_model(
        self,
        model,
        item_id: int,
    ):
        self.logger.debug(
            f"Starting to fetch element with ID: {item_id} for {model.__name__}"
        )
        try:
            async with self.db.async_session() as session:
                result = await session.execute(
                    select(model).where(getattr(model, "id") == item_id)
                )
                item = result.scalars().one_or_none()
                if item is not None:
                    self.logger.debug(
                        f"Fetched element with ID {item_id} for {model.__name__}: {item.__dict__}"
                    )
                else:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for {model.__name__}"
                    )
                return item
        except Exception as ex:
            self.logger.error(
                f"Error fetching element with ID: {item_id} for {model.__name__}: {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch element for model id:{item_id} {self.model.__name__}.",
            )

    # async def get_by_id_and_model(
    #     self,
    #     model,
    #     item_id: int,
    # ):
    #     async with self.db.async_session() as session:
    #         result = await session.execute(
    #             select(model).where(getattr(model, "id") == item_id)
    #         )
    #         item = result.scalars().one_or_none()
    #         return item

    async def update(self, item_id: int, item, **kwargs):
        self.logger.debug(f"Starting to update element with ID: {item_id}")
        async with self.db.async_session() as session:
            try:
                updated_item = await self.get_by_id(item_id)
                if not updated_item:
                    self.logger.warning(
                        f"No element found with ID: {item_id} for model {self.model.__name__}"
                    )
                    return None

                for key, value in item.dict(exclude_unset=True).items():
                    setattr(updated_item, key, value)

                await session.execute(
                    update(self.model)
                    .where(self.model.id == item_id)
                    .values(item.dict(exclude_unset=True))
                )

                await session.commit()
                updated_item = await self.get_by_id(item_id)
                self.logger.info(
                    f"Updated element with ID: {item_id}: {updated_item.__dict__}"
                )
                return updated_item
            except Exception as ex:
                self.logger.error(
                    f"Error updating element with ID: {item_id} for model {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update element for model id:{item_id} {self.model.__name__}.",
                )

    async def delete(self, item_id: int):
        self.logger.debug(f"Starting to delete element with ID: {item_id}")
        async with self.db.async_session() as session:
            try:
                db_item = await self.get_by_id(item_id)
                if not db_item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{self.model.__name__} not found",
                    )
                await session.delete(db_item)
                await session.commit()
                self.logger.info(
                    f"Deleted element with ID: {item_id}: {db_item.__dict__}"
                )
                return db_item
            except Exception as ex:
                self.logger.error(
                    f"Error deleting element with ID: {item_id} for model {self.model.__name__}: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete element for model id:{item_id} {self.model.__name__}.",
                )

    async def get_item_by_field_value(self, value, field_name: str):
        self.logger.debug(
            f"Starting to fetch item by field {field_name} with value: {value} for model {self.model.__name__}"
        )
        async with self.db.async_session() as session:
            try:
                # Access the column directly from the model
                column: Column = getattr(self.model, field_name)
                self.logger.info(
                    f"Accessed column: {column} for model {self.model.__name__}"
                )

                stmt = select(self.model).where(column == value)
                self.logger.debug(
                    f"Executing SQL statement: {stmt} for model {self.model.__name__}"
                )

                result: Result = await session.execute(stmt)
                self.logger.debug(
                    f"Query result: {result} for model {self.model.__name__}"
                )

                return result.scalars().one_or_none()
            except Exception as ex:
                self.logger.error(
                    f"Error fetching item by {field_name} with value {value}: {ex} for model {self.model.__name__}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch item for model {self.model.__name__}. Please try again later.",
                )

    # async def get_item_by_field_value(self, value, field_name: str):
    #     async with self.db.async_session() as session:
    #         # Access the column directly from the model
    #         column: Column = getattr(self.model, field_name)
    #         print("Column: ", column)
    #
    #         stmt = select(self.model).where(column == value)
    #         result: Result = await session.execute(stmt)
    #         print(result)
    #         return result.scalars().one_or_none()

    async def update_item_by_eesl_id(
        self,
        eesl_field_name: str,
        eesl_value: int,
        new_item,
    ):
        async with self.db.async_session() as session:
            self.logger.info(
                f"Starting update_item_by_eesl_id with eesl_field_name: {eesl_field_name}, eesl_value: {eesl_value} for model {self.model.__name__}"
            )
            is_exist = await self.get_item_by_field_value(
                eesl_value,
                eesl_field_name,
            )
            if is_exist:
                self.logger.debug(
                    f"Item found with id: {is_exist.id} for model {self.model.__name__}"
                )
                update_dict = {}
                for key, value in new_item.__dict__.items():
                    if not key.startswith("_"):
                        update_dict[key] = value
                await session.execute(
                    update(self.model)
                    .where(getattr(self.model, eesl_field_name) == eesl_value)
                    .values(update_dict)
                )
                self.logger.debug(
                    f"Update operation executed for item with id: {is_exist.id} for model {self.model.__name__}"
                )
                await session.commit()
                find_updated = await self.get_by_id(is_exist.id)
                self.logger.info(
                    f"Updated item retrieved with id: {find_updated.id} for model {self.model.__name__}"
                )
                return find_updated
            else:
                self.logger.error(f"No item found for model {self.model.__name__}")
                return None

    # async def update_item_by_eesl_id(
    #     self,
    #     eesl_field_name: str,
    #     eesl_value: int,
    #     new_item,
    # ):
    #     async with self.db.async_session() as session:
    #         is_exist = await self.get_item_by_field_value(
    #             eesl_value,
    #             eesl_field_name,
    #         )
    #         if is_exist:
    #             update_dict = {}
    #             for key, value in new_item.__dict__.items():
    #                 if not key.startswith("_"):
    #                     update_dict[key] = value
    #             await session.execute(
    #                 update(self.model)
    #                 .where(getattr(self.model, eesl_field_name) == eesl_value)
    #                 .values(update_dict)
    #             )
    #             await session.commit()
    #             find_updated = await self.get_by_id(is_exist.id)
    #             # print('find_updated: ', find_updated)
    #             return find_updated
    #         else:
    #             # print('NONE')
    #             return None

    async def find_relation(
        self,
        secondary_table: TextClause,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ):
        async with self.db.async_session() as session:
            self.logger.debug(f"Starting find_relation for model {self.model.__name__}")
            # Check if the relation already exists
            existing_relation = await session.execute(
                select(secondary_table).filter(
                    (getattr(self.model, field_name_one) == fk_item_one)
                    & (getattr(self.model, field_name_two) == fk_item_two)
                )
            )
            result = existing_relation.scalar()
            if result:
                self.logger.info(
                    f"Relation found {existing_relation.__dict__} for model {self.model.__name__}"
                )
            else:
                self.logger.debug(f"No relation found for model {self.model.__name__}")
            return result

    # async def find_relation(
    #     self,
    #     secondary_table: TextClause,
    #     fk_item_one: int,
    #     fk_item_two: int,
    #     field_name_one: str,
    #     field_name_two: str,
    # ):
    #     async with self.db.async_session() as session:
    #         # Check if the relation already exists
    #         existing_relation = await session.execute(
    #             select(secondary_table).filter(
    #                 (getattr(self.model, field_name_one) == fk_item_one)
    #                 & (getattr(self.model, field_name_two) == fk_item_two)
    #             )
    #         )
    #         return existing_relation.scalar()

    async def is_relation_exist(
        self,
        secondary_table,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ) -> bool:
        self.logger.debug(
            f"Checking if relation exists for model {self.model.__name__}"
        )
        existing_record = await self.find_relation(
            secondary_table,
            fk_item_one,
            fk_item_two,
            field_name_one,
            field_name_two,
        )
        if existing_record:
            self.logger.debug(
                f"Relation found {existing_record.__dict__} for model {self.model.__name__}"
            )
            return True
        else:
            self.logger.debug(f"No relation found for model {self.model.__name__}")
            return False

    # async def is_relation_exist(
    #     self,
    #     secondary_table,
    #     fk_item_one: int,
    #     fk_item_two: int,
    #     field_name_one: str,
    #     field_name_two: str,
    # ) -> bool:
    #     existing_record = await self.find_relation(
    #         secondary_table,
    #         fk_item_one,
    #         fk_item_two,
    #         field_name_one,
    #         field_name_two,
    #     )
    #     if existing_record:
    #         return True
    #     return False

    async def create_m2m_relation(
        self,
        parent_model,
        child_model,
        secondary_table: TextClause,
        parent_id: int,
        child_id: int,
        parent_id_name: str,
        child_id_name: str,
        child_relation,
    ):
        async with self.db.async_session() as session:
            existing_relation = await self.is_relation_exist(
                secondary_table,
                parent_id,
                child_id,
                parent_id_name,
                child_id_name,
            )

            if existing_relation:
                self.logger.warning(
                    f"Parent {parent_model.__name__}-{child_model.__name__} relation already exists for model {self.model.__name__}"
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"{parent_model.__name__}-{child_model.__name__} relation "
                    f"already exists for model {self.model.__name__}",
                )

            parent = await session.scalar(
                select(parent_model)
                .where(parent_model.id == parent_id)
                .options(selectinload(getattr(parent_model, child_relation))),
            )
            if parent:
                self.logger.debug(
                    f"Parent {parent_model.__name__} found with id: {parent_id} for model {self.model.__name__}"
                )
                child = await session.execute(
                    select(child_model).where(child_model.id == child_id)
                )
                child_new = child.scalar()
                if child_new:
                    self.logger.debug(
                        f"Child {child_model.__name__} found with id: {child_id} for model {self.model.__name__}"
                    )
                    try:
                        getattr(parent, child_relation).append(child_new)
                        await session.commit()
                        self.logger.info(
                            f"Relation created between {parent_model.__name__} and {child_model.__name__} for model {self.model.__name__}"
                        )
                        return list(getattr(parent, child_relation))
                    except Exception as ex:
                        self.logger.error(
                            f"Error creating relation: {ex} for model {self.model.__name__}",
                            exc_info=True,
                        )
                        return None
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{child_model.__name__} id:{child_id} for model {self.model.__name__} not found",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"{parent_model.__name__} id:{parent_id} for model {self.model.__name__} not found",
                )

    # async def create_m2m_relation(
    #     self,
    #     parent_model,
    #     child_model,
    #     secondary_table: TextClause,
    #     parent_id: int,
    #     child_id: int,
    #     parent_id_name: str,
    #     child_id_name: str,
    #     child_relation,
    # ):
    #     async with self.db.async_session() as session:
    #         existing_relation = await self.is_relation_exist(
    #             secondary_table,
    #             parent_id,
    #             child_id,
    #             parent_id_name,
    #             child_id_name,
    #         )
    #
    #         if existing_relation:
    #             raise HTTPException(
    #                 status_code=409,
    #                 detail=f"{parent_model.__name__}-{child_model.__name__} relation "
    #                 f"already exists",
    #             )
    #
    #         parent = await session.scalar(
    #             select(parent_model)
    #             .where(parent_model.id == parent_id)
    #             .options(selectinload(getattr(parent_model, child_relation))),
    #         )
    #         if parent:
    #             child = await session.execute(
    #                 select(child_model).where(child_model.id == child_id)
    #             )
    #             child_new = child.scalar()
    #             # print(child_new.id)
    #             if child_new:
    #                 try:
    #                     getattr(parent, child_relation).append(child_new)
    #                     await session.commit()
    #                     return list(getattr(parent, child_relation))
    #                 except Exception as ex:
    #                     raise ex
    #             else:
    #                 raise HTTPException(
    #                     status_code=404,
    #                     detail=f"{child_model.__name__} id:{child_id} not found",
    #                 )
    #         else:
    #             raise HTTPException(
    #                 status_code=404,
    #                 detail=f"{parent_model.__name__} id:{parent_id} not found",
    #             )

    async def get_related_items(
        self,
        item_id: int,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related items for item id: {item_id} for model {self.model.__name__}"
                )
                item = await session.execute(
                    select(self.model).where(self.model.id == item_id)
                )
                result = item.scalars().one_or_none()
                if result:
                    self.logger.debug(
                        f"Related item found with id: {result.id} for model {self.model.__name__}"
                    )
                else:
                    self.logger.debug(
                        f"No related item found for id: {item_id} for model {self.model.__name__}"
                    )
                return result
            except NoResultFound:
                self.logger.warning(
                    f"No result found for item id: {item_id} for model {self.model.__name__}"
                )
                return None

    # async def get_related_items(
    #     self,
    #     item_id: int,
    # ):
    #     async with self.db.async_session() as session:
    #         try:
    #             item = await session.execute(
    #                 select(self.model).where(self.model.id == item_id)
    #             )
    #             return item.scalars().one_or_none()
    #         except NoResultFound:
    #             return None

    # async def get_related_items_level_one_by_id(
    #     self,
    #     item_id: int,
    #     related_property: str,
    # ):
    #     async with self.db.async_session() as session:
    #         try:
    #             item = await session.execute(
    #                 select(self.model)
    #                 .where(self.model.id == item_id)
    #                 .options(selectinload(getattr(self.model, related_property)))
    #                 # .options(joinedload(getattr(self.model, related_property)))
    #             )
    #             return getattr(item.scalars().one(), related_property)
    #         except NoResultFound:
    #             return None

    async def get_related_item_level_one_by_id(
        self,
        item_id: int,
        related_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related items for item id one level: {item_id} and property: {related_property} "
                    f"for model {self.model.__name__}"
                )
                item = await session.execute(
                    select(self.model)
                    .where(self.model.id == item_id)
                    .options(selectinload(getattr(self.model, related_property)))
                    # .options(joinedload(getattr(self.model, related_property)))
                )
                result = getattr(item.scalars().one(), related_property)
                if result:
                    self.logger.debug(
                        f"Related item {result} found for property: {related_property} "
                        f"for model {self.model.__name__}"
                    )
                else:
                    self.logger.debug(
                        f"No related item found one level for property: {related_property} "
                        f"for model {self.model.__name__}"
                    )
                return result
            except NoResultFound:
                self.logger.warning(
                    f"No result found for item id one level: {item_id} and property: {related_property} "
                    f"for model {self.model.__name__}"
                )
                return None

    async def get_nested_related_item_by_id(
        self,
        item_id: int,
        service: Any,
        related_property: str,
        nested_related_property: str,
    ):
        related_item = await self.get_related_item_level_one_by_id(
            item_id, related_property
        )

        if related_item is not None:
            _id = related_item.id
            self.logger.debug(
                f"Fetching nested related items for item id: {_id} and property: {related_property} "
                f"and nested_related_property {nested_related_property} for model {self.model.__name__}"
            )
            item = await service.get_related_item_level_one_by_id(
                _id, nested_related_property
            )
            self.logger.debug(
                f"Related item {item} found for item id: {_id} "
                f"and nested_related_property: {nested_related_property} for model {self.model.__name__}"
            )
            return item
        self.logger.warning(
            f"No result found for item id: {item_id} and property: {related_property} "
            f"and nested_related_property {nested_related_property} for model {self.model.__name__}"
        )
        return None

    # async def get_nested_related_item_by_id(
    #     self,
    #     item_id: int,
    #     service: Any,
    #     related_property: str,
    #     nested_related_property: str,
    # ):
    #     related_item = await self.get_related_item_level_one_by_id(
    #         item_id, related_property
    #     )
    #
    #     if related_item is not None:
    #         _id = related_item.id
    #         items = await service.get_related_item_level_one_by_id(
    #             _id, nested_related_property
    #         )
    #         return items
    #
    #     return None

    async def get_related_item_level_one_by_key_and_value(
        self,
        filter_key: str,
        filter_value: Any,
        related_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related items for key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                item = await session.execute(
                    select(self.model)
                    .where(getattr(self.model, filter_key) == filter_value)
                    .options(selectinload(getattr(self.model, related_property)))
                )
                result = getattr(item.scalars().one(), related_property)
                if result:
                    self.logger.debug(
                        f"Related item found {result} for property: {related_property} for model {self.model.__name__}"
                    )
                else:
                    self.logger.debug(
                        f"No related item found for property: {related_property} for model {self.model.__name__}"
                    )
                return result
            except NoResultFound:
                self.logger.warning(
                    f"No result found for key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                return None

    async def get_related_items_by_two(
        self,
        filter_key: str,
        filter_value: Any,
        second_model,
        related_property: str,
        second_level_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Fetching related item by two level for "
                    f"key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                )
                query = (
                    select(self.model)
                    .where(getattr(self.model, filter_key) == filter_value)
                    .options(
                        selectinload(getattr(self.model, related_property)).joinedload(
                            getattr(second_model, second_level_property)
                        )
                    )
                )

                result = await session.execute(query)
                item = result.unique().scalars().one_or_none()

                if item:
                    self.logger.debug(
                        f"Item {item} found for "
                        f"key: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                    )
                    related_items = getattr(item, related_property)
                    items = []
                    for related_item in related_items:
                        for final_point in getattr(related_item, second_level_property):
                            items.append(final_point)
                    return items
                else:
                    self.logger.warning(
                        f"No item found for "
                        f"ey: {filter_key} and value: {filter_value} for model {self.model.__name__}"
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"{second_model} {filter_key} not found for model {self.model.__name__}",
                    )
            except Exception as e:
                self.logger.error(
                    f"Error fetching related item for key: {filter_key} and value {filter_value} "
                    f"for model {self.model.__name__}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal Server Error {e}",
                )

    @staticmethod
    def is_des(descending, order):
        try:
            if descending:
                db_logger_helper.debug("Setting order to descending")
                return order.desc()
            else:
                db_logger_helper.debug("Setting order to ascending")
                return order.asc()
        except Exception as e:
            db_logger_helper.error(f"Error setting order: {e}", exc_info=True)
            return None

    @staticmethod
    def default_serializer(obj):
        try:
            if isinstance(obj, datetime):
                db_logger_helper.debug(f"Serializing datetime object: {obj}")
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        except Exception as e:
            db_logger_helper.error(
                f"Error serializing object {obj}: {e}", exc_info=True
            )
            return None

    @staticmethod
    def to_dict(model):
        try:
            if isinstance(model, dict):
                db_logger_helper.debug("Model is already a dictionary")
                return model
            elif isinstance(model, Base):
                data = {
                    column.name: getattr(model, column.name)
                    for column in model.__table__.columns
                }
                db_logger_helper.debug(f"Extracted data from model: {data}")
                data.pop("_sa_instance_state", None)
                return data
            else:
                raise TypeError("Unsupported type")
        except Exception as e:
            db_logger_helper.error(
                f"Error converting model {model} to dictionary: {e}", exc_info=True
            )
            return None

    @staticmethod
    async def upload_file(self, upload_file: UploadFile):
        self.logger.debug(f"Current Working Directory for uploading: {os.getcwd()}")

        # Use an absolute path for the upload directory
        upload_dir = Path("/static/uploads")

        self.logger.debug(
            f"Upload Directory: {upload_dir.resolve()} and file name {upload_file.filename}"
        )

        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(
                f"Does the upload directory exist after mkdir: {upload_dir.exists()}"
            )
            dest = upload_dir / upload_file.filename
            self.logger.debug(f"Destination path: {dest}")

            with dest.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
            self.logger.debug(f"Does the file exist after writing: {dest.exists()}")
            self.logger.info(f"File saved to {dest}")
            return {"filename": upload_file.filename, "url": str(dest)}
        except Exception as e:
            self.logger.error(f"Error type: {type(e)}")
            self.logger.error(f"Error uploading file args: {e.args}", exc_info=True)
            return HTTPException(
                status_code=500,
                detail=f"Internal Server Error Uploading file: {str(e)}",
            )


class Base(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)
