import os
import asyncio
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict
from starlette.websockets import WebSocket
import asyncpg
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    selectinload,
)

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from fastapi import HTTPException, UploadFile
from sqlalchemy import select, update, Result, Column, Table, TextClause

from src.core.config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('WebSocketManager')


# DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{str(port)}/{db_name}"


class Database:
    def __init__(self, db_url: str, echo: bool = False):
        self.engine = create_async_engine(url=db_url, echo=echo)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )


async def get_db_session():
    async with db.async_session() as session:
        async with session.begin():
            yield session


db = Database(db_url=settings.db.db_url, echo=settings.db_echo)


class MatchDataWebSocketManager:
    def __init__(self, db_url):
        self.db_url = db_url
        self.connection = None
        self.match_data_queues = {}
        self.playclock_queues = {}
        self.gameclock_queues = {}
        self.logger = logging.getLogger('WebSocketManager')
        self.logger.info('WebSocketManager initialized')

    async def connect(self, client_id: str):
        self.match_data_queues[client_id] = asyncio.Queue()
        self.playclock_queues[client_id] = asyncio.Queue()
        self.gameclock_queues[client_id] = asyncio.Queue()

    async def disconnect(self, client_id: str):
        del self.match_data_queues[client_id]
        del self.playclock_queues[client_id]
        del self.gameclock_queues[client_id]

    async def startup(self):
        self.connection = await asyncpg.connect(self.db_url)
        await self.connection.add_listener('matchdata_change', self.match_data_listener)
        await self.connection.add_listener('match_change', self.match_data_listener)
        await self.connection.add_listener('scoreboard_change', self.match_data_listener)
        await self.connection.add_listener('playclock_change', self.playclock_listener)
        await self.connection.add_listener('gameclock_change', self.gameclock_listener)

    async def playclock_listener(self, connection, pid, channel, payload):
        print("[Playclock listener] Start")
        if not payload or not payload.strip():
            self.logger.warning('No payload received')
            return

        data = json.loads(payload.strip())
        match_id = data['match_id']
        data['type'] = 'playclock-update'
        self.logger.debug(
            f'''Match ID: {match_id}
            Received playclock payload: {payload}
            connection: {connection}
            pid: {pid}
            channel: {channel}
            data: {data}
            ''')

        # for queue in self.playclock_queues.values():
        #     await queue.put(data)

        await connection_manager.send_to_all(data, match_id=match_id)

    async def gameclock_listener(self, connection, pid, channel, payload):
        print(f"[Gameclock listener] Start")
        if not payload or not payload.strip():
            self.logger.warning('No payload received')
            return

        data = json.loads(payload.strip())
        match_id = data['match_id']
        data['type'] = 'gameclock-update'
        self.logger.debug(
            f'''Match ID: {match_id}
            Received gameclock payload: {payload}        
            connection: {connection}
            pid: {pid}
            channel: {channel}
            data: {data}
            ''')

        # for queue in self.gameclock_queues.values():
        #     await queue.put(data)

        await connection_manager.send_to_all(data, match_id=match_id)

    async def match_data_listener(self, connection, pid, channel, payload):
        print("[Match Data Listener] Start")
        if not payload or not payload.strip():
            self.logger.warning('No payload received')
            return

        data = json.loads(payload.strip())
        match_id = data['match_id']
        data['type'] = 'match-update'
        self.logger.debug(
            f'''Match ID: {match_id}
            Received match data payload: {payload}        
            connection: {connection}
            pid: {pid}
            channel: {channel}
            data: {data}
            ''')
        # for queue in self.match_data_queues.values():
        #     await queue.put(data)

        # await connection_manager.send_to_all(data)

        await connection_manager.send_to_all(data, match_id=match_id)

    async def shutdown(self):
        if self.connection:
            await self.connection.close()


ws_manager = MatchDataWebSocketManager(db_url=settings.db.db_url_websocket())


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.queues: Dict[str, asyncio.Queue] = {}
        self.match_subscriptions: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, match_id: str = None):
        print(f'Active Connections: {len(self.active_connections)}')

        if client_id in self.active_connections:
            await self.active_connections[client_id].close()

        self.active_connections[client_id] = websocket
        self.queues[client_id] = asyncio.Queue()

        if match_id:
            if match_id in self.match_subscriptions:
                self.match_subscriptions[match_id].append(client_id)
                print(f'match subscription match id:{match_id}', self.match_subscriptions)
            else:
                self.match_subscriptions[match_id] = [client_id]
                print(f'match subscription client_id{client_id}', self.match_subscriptions)

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].close()
            del self.active_connections[client_id]
            del self.queues[client_id]

            for match_id in self.match_subscriptions:
                if client_id in self.match_subscriptions[match_id]:
                    self.match_subscriptions[match_id].remove(client_id)

    async def send_to_all(self, data: str, match_id: str = None):
        print(f"[Debug][send_to_all] Entered method with data: {data}, match_id: {match_id}")
        print(f"[Debug][send_to_all] Current match_subscriptions: {self.match_subscriptions}")
        if match_id:
            for client_id in self.match_subscriptions.get(match_id, []):
                print(f"[Debug][send_to_all] Checking client_id: {client_id}")
                if client_id in self.queues:
                    print(f"[Debug][send_to_all] Adding data to queue of client_id: {client_id}")
                    await self.queues[client_id].put(data)
                    print(f"[send_to_all_{match_id}] Data sent to all client queues with match id:{match_id}", data)
                # print("[send_to_all] Data sent to all client queues:", data)

    async def send_to_match_id_channels(self, data):
        match_id = data['match_id']
        await connection_manager.send_to_all(data, match_id=match_id)


connection_manager = ConnectionManager()


class BaseServiceDB:
    def __init__(self, database, model):
        self.db = database
        self.model = model

    async def create(self, item):
        async with self.db.async_session() as session:
            try:
                session.add(item)
                await session.commit()
                await session.refresh(item)
                return item
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"{self.model.__name__} creation error."
                           f"Check input data.",
                )

    async def get_all_elements(
            self,
            skip: int = 0,
            limit: int = 500,
            order_by: str = "id",
            descending: bool = False,
    ):
        async with self.db.async_session() as session:
            order = getattr(self.model, order_by)
            new_order = self.is_des(descending, order)

            stmt = select(self.model).offset(skip).limit(limit).order_by(new_order)

            items = await session.execute(stmt)
            result = items.scalars().all()
            return list(result)

    async def get_by_id(
            self,
            item_id: int,
    ):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == item_id)
            )
            model = result.scalars().one_or_none()
            # print(
            #     f"Type of model: {self.model.__name__}"
            # )  # Add this line for debugging
            # print(model)
            return model

    async def get_by_id_and_model(
            self,
            model,
            item_id: int,
    ):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(model).where(getattr(model, "id") == item_id)
            )
            item = result.scalars().one_or_none()
            # print(
            #     f"Type of model: {self.model.__name__}"
            # )  # Add this line for debugging
            # print(model)
            return item

    # async def update(self, item_id: int, item, **kwargs):
    #     async with self.db.async_session() as session:
    #         db_item = await self.get_by_id(item_id)
    #         if not db_item:
    #             return None
    #
    #         for key, value in item.dict(exclude_unset=True).items():
    #             # Check if the value is a string and represents a boolean
    #             if isinstance(value, str) and value.lower() in ['true', 'false']:
    #                 # Convert string 'true' or 'false' to boolean
    #                 value = value.lower() == 'true'
    #
    #             setattr(db_item, key, value)
    #
    #         await session.execute(
    #             update(self.model)
    #             .where(self.model.id == item_id)
    #             .values(item.dict(exclude_unset=True))
    #         )
    #
    #         await session.commit()
    #         updated_item = await self.get_by_id(db_item.id)
    #         return updated_item

    async def update(self, item_id: int, item, **kwargs):
        async with self.db.async_session() as session:
            db_item = await self.get_by_id(item_id)
            # print(db_item)
            if not db_item:
                return None
            # print(db_item)
            for key, value in item.dict(exclude_unset=True).items():
                # print(key, value)
                setattr(db_item, key, value)
            await session.execute(
                update(self.model)
                .where(self.model.id == item_id)
                .values(item.dict(exclude_unset=True))
            )

            await session.commit()
            updated_item = await self.get_by_id(db_item.id)
            return updated_item

    async def delete(self, item_id: int):
        async with self.db.async_session() as session:
            db_item = await self.get_by_id(item_id)
            if not db_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"{self.model.__name__} not found",
                )
            await session.delete(db_item)
            await session.commit()
            raise HTTPException(
                status_code=200,
                detail=f"{self.model.__name__} {db_item.id} deleted",
            )

    async def get_item_by_field_value(self, value, field_name: str):
        async with self.db.async_session() as session:
            # Access the column directly from the model
            column: Column = getattr(self.model, field_name)
            print('Column: ', column)

            stmt = select(self.model).where(column == value)
            result: Result = await session.execute(stmt)
            print(result)
            return result.scalars().one_or_none()

    # async def get_items_by_attribute(
    #     self,
    #     value,
    #     field_name: str,
    #     order_by: str = "id",
    #     descending: bool = False,
    #     skip=0,
    #     limit=100,
    # ):
    #     async with self.db.async_session() as session:
    #         order = getattr(self.model, order_by)
    #         new_order = self.is_des(descending, order)
    #         column: Column = getattr(self.model, field_name)
    #
    #         stmt = (
    #             select(self.model)
    #             .where(column == value)
    #             .offset(skip)
    #             .limit(limit)
    #             .order_by(new_order)
    #         )
    #
    #         items = await session.execute(stmt)
    #         result = []
    #         for item in items.scalars().fetchall():
    #             result.append(item.__dict__)
    #         return result

    async def update_item_by_eesl_id(
            self,
            eesl_field_name: str,
            eesl_value: int,
            new_item,
    ):
        async with self.db.async_session() as session:
            is_exist = await self.get_item_by_field_value(
                eesl_value,
                eesl_field_name,
            )
            if is_exist:
                update_dict = {}
                for key, value in new_item.__dict__.items():
                    if not key.startswith("_"):
                        update_dict[key] = value
                await session.execute(
                    update(self.model)
                    .where(getattr(self.model, eesl_field_name) == eesl_value)
                    .values(update_dict)
                )
                await session.commit()
                find_updated = await self.get_by_id(is_exist.id)
                # print('find_updated: ', find_updated)
                return find_updated
            else:
                # print('NONE')
                return None

    async def find_relation(
            self,
            secondary_table: TextClause,
            fk_item_one: int,
            fk_item_two: int,
            field_name_one: str,
            field_name_two: str,
    ):
        async with self.db.async_session() as session:
            # Check if the relation already exists
            existing_relation = await session.execute(
                select(secondary_table).filter(
                    (getattr(self.model, field_name_one) == fk_item_one)
                    & (getattr(self.model, field_name_two) == fk_item_two)
                )
            )

            return existing_relation.scalar()

    async def is_relation_exist(
            self,
            secondary_table,
            fk_item_one: int,
            fk_item_two: int,
            field_name_one: str,
            field_name_two: str,
    ) -> bool:
        existing_record = await self.find_relation(
            secondary_table,
            fk_item_one,
            fk_item_two,
            field_name_one,
            field_name_two,
        )
        if existing_record:
            return True
        return False

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
                raise HTTPException(
                    status_code=409,
                    detail=f"{parent_model.__name__}-{child_model.__name__} relation "
                           f"already exists",
                )

            parent = await session.scalar(
                select(parent_model)
                .where(parent_model.id == parent_id)
                .options(selectinload(getattr(parent_model, child_relation))),
            )
            if parent:
                child = await session.execute(
                    select(child_model).where(child_model.id == child_id)
                )
                child_new = child.scalar()
                # print(child_new.id)
                if child_new:
                    try:
                        getattr(parent, child_relation).append(child_new)
                        await session.commit()
                        return list(getattr(parent, child_relation))
                    except Exception as ex:
                        raise ex
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"{child_model.__name__} id:{child_id} not found",
                    )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"{parent_model.__name__} id:{parent_id} not found",
                )

    async def get_related_items(
            self,
            item_id: int,
    ):
        async with self.db.async_session() as session:
            try:
                item = await session.execute(
                    select(self.model).where(self.model.id == item_id)
                )
                return item.scalars().one_or_none()
            except NoResultFound:
                return None

    # async def get_related_items_level_one_by_id(
    #         self,
    #         item_id: int,
    #         related_property: str,
    #         nested_related_property: str = None,
    # ):
    #     async with self.db.async_session() as session:
    #         try:
    #             query = select(self.model) \
    #                 .where(self.model.id == item_id) \
    #                 .options(selectinload(getattr(self.model, related_property)))
    #             if nested_related_property:
    #                 query = query.options(
    #                     selectinload(getattr(self.model, related_property + '.' + nested_related_property)))
    #             item = await session.execute(query)
    #             return getattr(item.scalars().one(), related_property)
    #         except NoResultFound:
    #             return None

    async def get_related_items_level_one_by_id(
            self,
            item_id: int,
            related_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                item = await session.execute(
                    select(self.model)
                    .where(self.model.id == item_id)
                    .options(selectinload(getattr(self.model, related_property)))
                    # .options(joinedload(getattr(self.model, related_property)))

                )
                return getattr(item.scalars().one(), related_property)
            except NoResultFound:
                return None

    async def get_nested_related_items_by_id(
            self,
            item_id: int,
            service: Any,
            related_property: str,
            nested_related_property: str,
    ):
        related_item = await self.get_related_items_level_one_by_id(
            item_id, related_property
        )

        if related_item is not None:
            _id = related_item.id
            items = await service.get_related_items_level_one_by_id(_id, nested_related_property)
            return items

        return None

    async def get_related_items_level_one_by_key_and_value(
            self,
            filter_key: str,
            filter_value: Any,
            related_property: str,
    ):
        async with self.db.async_session() as session:
            try:
                item = await session.execute(
                    select(self.model)
                    .where(getattr(self.model, filter_key) == filter_value)
                    .options(selectinload(getattr(self.model, related_property)))
                )
                return getattr(item.scalars().one(), related_property)
            except NoResultFound:
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

            items = []
            if item:
                related_items = getattr(item, related_property)
                for related_item in related_items:
                    for final_point in getattr(related_item, second_level_property):
                        items.append(final_point)
                return items
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"{second_model} {filter_key} not found",
                )

    @staticmethod
    def is_des(descending, order):
        if descending:
            order = order.desc()
        else:
            order = order.asc()
        return order

    @staticmethod
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def to_dict(model):
        if isinstance(model, dict):
            return model
        elif isinstance(model, Base):  # replace with your model's superclass if needed
            data = {
                column.name: getattr(model, column.name)
                for column in model.__table__.columns
            }
            data.pop("_sa_instance_state", None)
            return data
        else:
            raise TypeError("Unsupported type")

    async def upload_file(self, upload_file: UploadFile):
        print(f"Current Working Directory: {os.getcwd()}")

        # Use an absolute path for the upload directory
        upload_dir = Path("/static/uploads")

        print(f"Upload Directory: {upload_dir.resolve()}")

        try:
            # Ensure the upload directory exists
            upload_dir.mkdir(parents=True, exist_ok=True)
            print(f"Does the upload directory exist after mkdir: {upload_dir.exists()}")

            # Define the destination path
            dest = upload_dir / upload_file.filename
            print(f"Destination path: {dest}")

            # Write upload_file content into destination file
            with dest.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            # Check if the file exists after writing
            print(f"Does the file exist after writing: {dest.exists()}")

            # Provide upload_file information
            print(f"File saved to {dest}")
            return {"filename": upload_file.filename, "url": str(dest)}
        except Exception as e:
            print(f"Error type: {type(e)}")
            print(f"Error args: {e.args}")
            return {"error": str(e)}


class Base(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)
