from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, PositionDB
from src.core.models.base import Database

from ..logging_config import get_logger, setup_logging
from .schemas import PositionSchemaCreate, PositionSchemaUpdate

setup_logging()
ITEM = "POSITION"


class PositionServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PositionDB)
        self.logger = get_logger("backend_logger_PositionServiceDB", self)
        self.logger.debug("Initialized PositionServiceDB")

    async def create(
        self,
        p: PositionSchemaCreate,
    ) -> PositionDB:
        try:
            self.logger.debug(f"Creating new {ITEM} {p}")
            position = self.model(
                sport_id=p.sport_id,
                title=p.title.upper(),
            )
            return await super().create(position)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Database error creating new position {p}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error creating new position {p}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as ex:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.create: {ex}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

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

    async def get_position_by_title(self, title: str) -> PositionDB:
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
