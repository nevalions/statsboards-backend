from fastapi import HTTPException

from src.core.models import BaseServiceDB, SponsorLineDB
from src.core.models.base import Database

from ..logging_config import get_logger, setup_logging
from .schemas import SponsorLineSchemaCreate, SponsorLineSchemaUpdate

setup_logging()
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
            result = self.model(
                title=item.title,
            )
            return await super().create(result)
        except Exception as e:
            self.logger.error(f"Error creating {ITEM}: {e}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating {self.model.__name__}. Check input data. {ITEM}",
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
