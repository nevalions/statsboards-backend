from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, PositionDB, handle_service_exceptions
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import PositionSchemaCreate, PositionSchemaUpdate
ITEM = "POSITION"


class PositionServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PositionDB)
        self.logger = get_logger("backend_logger_PositionServiceDB", self)
        self.logger.debug("Initialized PositionServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: PositionSchemaCreate,
    ) -> PositionDB:
        self.logger.debug(f"Creating new {ITEM} {item}")
        position = self.model(
            sport_id=item.sport_id,
            title=item.title.upper(),
        )
        return await super().create(position)

    async def update(
        self,
        item_id: int,
        item: PositionSchemaUpdate,
        **kwargs,
    ) -> PositionDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(item_name=ITEM, operation="fetching by title")
    async def get_position_by_title(self, title: str) -> PositionDB | None:
        async with self.db.async_session() as session:
            self.logger.debug(f"Getting position by title: {title}")
            stmt = select(PositionDB).where(
                func.lower(func.trim(PositionDB.title)) == title.lower().strip()
            )
            results = await session.execute(stmt)
            return results.scalars().one_or_none()
