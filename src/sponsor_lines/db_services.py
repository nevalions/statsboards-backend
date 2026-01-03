from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.models import BaseServiceDB, SponsorLineDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import SponsorLineSchemaCreate, SponsorLineSchemaUpdate

ITEM = "SPONSOR_LINE"


class SponsorLineServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, SponsorLineDB)
        self.logger = get_logger("backend_logger_SponsorLineServiceDB", self)
        self.logger.debug("Initialized SponsorLineServiceDB")

    async def create(
        self,
        item: SponsorLineSchemaCreate,
    ) -> SponsorLineDB:
        try:
            self.logger.debug(f"Creating {ITEM}")
            return await super().create(item)
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as e:
            self.logger.error(f"Database error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Database error creating {self.model.__name__}",
            )
        except (ValueError, KeyError, TypeError) as e:
            self.logger.warning(f"Data error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided",
            )
        except Exception as e:
            self.logger.critical(
                f"Unexpected error in {self.__class__.__name__}.create: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error",
            )

    async def update(
        self,
        item_id: int,
        item: SponsorLineSchemaUpdate,
        **kwargs,
    ) -> SponsorLineDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
