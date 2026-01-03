from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, SponsorDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import SponsorSchemaCreate, SponsorSchemaUpdate

ITEM = "SPONSOR"


class SponsorServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, SponsorDB)
        self.logger = get_logger("backend_logger_SponsorServiceDB", self)
        self.logger.debug("Initialized SponsorServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: SponsorSchemaCreate,
    ) -> SponsorDB:
        self.logger.debug(f"Creating {ITEM} {item}")
        return await super().create(item)

    async def update(
        self,
        item_id: int,
        item: SponsorSchemaUpdate,
        **kwargs,
    ) -> SponsorDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
