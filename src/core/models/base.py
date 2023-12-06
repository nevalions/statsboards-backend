from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from fastapi import HTTPException
from sqlalchemy import select, update, Result, Column

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

    async def get_by_id(self, item_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == item_id)
            )
            model = result.scalars().one_or_none()
            print(
                f"Type of model: {self.model.__name__}"
            )  # Add this line for debugging
            return model

    async def update(self, item_id: int, item, **kwargs):
        async with self.db.async_session() as session:
            db_item = await self.get_by_id(item_id)
            if not db_item:
                return None

            for key, value in item.dict(exclude_unset=True).items():
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
                    status_code=404, detail=f"{self.model.__name__} not found"
                )
            await session.delete(db_item)
            await session.commit()
            raise HTTPException(
                status_code=200, detail=f"{self.model.__name__} {db_item.id} deleted"
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

    async def update_item_by_eesl_id(self, item, eesl_field_name: str, eesl_value: int):
        async with self.db.async_session() as session:
            is_exist = await self.get_item_by_field_value(eesl_value, eesl_field_name)
            if is_exist:
                for key, value in item.dict(exclude_unset=True).items():
                    setattr(is_exist, key, value)
                await session.execute(
                    update(self.model)
                    .where(getattr(self.model, eesl_field_name) == eesl_value)
                    .values(item.dict(exclude_unset=True))
                )
                await session.commit()
                find_updated = await self.get_by_id(is_exist.id)
                return find_updated
            else:
                return None

    async def find_relation(
        self,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ):
        async with self.db.async_session() as session:
            stmt = select(self.model).filter(
                getattr(self.model, field_name_one) == fk_item_one,
                getattr(self.model, field_name_two) == fk_item_two,
            )

            existing_record = await session.execute(stmt)
            return existing_record.scalars().one_or_none()

    async def is_relation_exist(
        self,
        fk_item_one: int,
        fk_item_two: int,
        field_name_one: str,
        field_name_two: str,
    ) -> bool:
        existing_record = await self.find_relation(
            fk_item_one, fk_item_two, field_name_one, field_name_two
        )
        if existing_record:
            return True
        return False

    @staticmethod
    def is_des(descending, order):
        if descending:
            order = order.desc()
        else:
            order = order.asc()
        return order


class Base(DeclarativeBase):
    __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(primary_key=True)
