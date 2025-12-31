import logging
from typing import Any, Callable

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
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

from src.core.config import settings
from src.core.models.mixins import (
    CRUDMixin,
    QueryMixin,
    RelationshipMixin,
    SerializationMixin,
)
from src.logging_config import get_logger
db_logger_helper = logging.getLogger("backend_logger_base_db")


class Database:
    def __init__(self, db_url: str, echo: bool = False):
        self.logger = get_logger("backend_logger_base_db", self)
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
        if field_name.endswith("_eesl_id"):
            return await self.update_item_by_eesl_id(
                field_name, field_value, item_schema
            )
        else:
            return await self.update(existing_item.id, item_schema)

    async def _create_item(self, item_schema, model_factory, **create_kwargs):
        if model_factory:
            return await self.create(model_factory(item_schema, **create_kwargs))
        else:
            schema_data = item_schema.model_dump(exclude_unset=True)
            model = self.model(**schema_data)
            return await self.create(model)


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
