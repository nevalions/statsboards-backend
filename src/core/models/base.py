from datetime import datetime
from typing import Any

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declared_attr,
    selectinload,
    joinedload,
)

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from fastapi import HTTPException
from sqlalchemy import select, update, Result, Column, Table, TextClause

from src.core.config import settings


# DATABASE_URL = f"postgresql+asyncpg://{user}:{password}@{host}:{str(port)}/{db_name}"


class Database:
    def __init__(self, db_url: str, echo: bool = False):
        self.engine = create_async_engine(url=db_url, echo=echo)
        self.async_session = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )


db = Database(db_url=settings.db.db_url, echo=settings.db_echo)


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
        limit: int = 100,
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

            stmt = select(self.model).where(column == value)
            result: Result = await session.execute(stmt)
            # print(result)
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
                return find_updated
            else:
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
                )
                return getattr(item.scalars().one(), related_property)
            except NoResultFound:
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
        data = {
            column.name: getattr(model, column.name)
            for column in model.__table__.columns
        }
        # Exclude the _sa_instance_state key
        data.pop("_sa_instance_state", None)
        return data


class Base(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)
