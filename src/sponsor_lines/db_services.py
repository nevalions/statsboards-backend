from src.core.models import BaseServiceDB, SponsorLineDB
from .schemas import SponsorLineSchemaUpdate, SponsorLineSchemaCreate
from ..logging_config import get_logger, setup_logging

setup_logging()
ITEM = "SPONSOR_LINE"


class SponsorLineServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, SponsorLineDB)
        self.logger = get_logger("backend_logger_SponsorLineServiceDB", self)
        self.logger.debug(f"Initialized SponsorLineServiceDB")

    async def create_sponsor_line(
        self,
        sponsor_line: SponsorLineSchemaCreate,
    ):
        try:
            self.logger.debug(f"Creating {ITEM}")
            result = self.model(
                title=sponsor_line.title,
            )
            return await super().create(result)
        except Exception as e:
            self.logger.error(f"Error creating {ITEM}: {e}")

    async def update_sponsor_line(
        self,
        item_id: int,
        item: SponsorLineSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
