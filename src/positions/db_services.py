from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.core.models import BaseServiceDB, PositionDB

from .schemas import PositionSchemaCreate, PositionSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "POSITION"


class PositionServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, PositionDB)
        self.logger = get_logger("backend_logger_PositionServiceDB", self)
        self.logger.debug(f"Initialized PositionServiceDB")

    async def create(
        self,
        p: PositionSchemaCreate,
    ):
        try:
            self.logger.debug(f"Creating new {ITEM} {p}")
            position = self.model(
                sport_id=p.sport_id,
                title=p.title.upper(),
            )
            return await super().create(position)
        except Exception as ex:
            self.logger.error(f"Error creating new position {p} {ex}", exc_info=True)

    async def update(
        self,
        item_id: int,
        item: PositionSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_position_by_title(self, title: str):
        async with self.db.async_session() as session:
            self.logger.debug(f"Getting position by title: {title}")
            try:
                stmt = select(PositionDB).where(
                    func.lower(func.trim(PositionDB.title)) == title.lower().strip()
                )
                results = await session.execute(stmt)
                position = results.scalars().one_or_none()
                if not position:
                    raise HTTPException(status_code=404, detail="Position not found")
                return position
            except HTTPException:
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Database error getting position by title: {title} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error fetching position by title: {title}",
                )
            except Exception as ex:
                self.logger.error(
                    f"Error getting position by title: {title} {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error fetching position by title: {title}",
                )
