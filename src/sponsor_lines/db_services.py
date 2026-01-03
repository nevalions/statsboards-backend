from src.core.decorators import handle_service_exceptions
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

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: SponsorLineSchemaCreate,
    ) -> SponsorLineDB:
        self.logger.debug(f"Creating {ITEM}")
        return await super().create(item)

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
