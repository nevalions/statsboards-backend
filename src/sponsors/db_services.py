from src.core.models import db, BaseServiceDB, SponsorDB
from src.logging_config import get_logger, setup_logging
from src.sponsors.schemas import SponsorSchemaUpdate, SponsorSchemaCreate


setup_logging()
ITEM = "SPONSOR"


class SponsorServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, SponsorDB)
        self.logger = get_logger("backend_logger_SponsorServiceDB", self)
        self.logger.debug(f"Initialized SponsorServiceDB")

    async def create_sponsor(
        self,
        t: SponsorSchemaCreate,
    ):
        try:
            self.logger.debug(f"Creating {ITEM} {t}")
            sponsor = self.model(
                title=t.title,
                logo_url=t.logo_url,
                scale_logo=t.scale_logo,
            )

            return await super().create(sponsor)
        except Exception as e:
            self.logger.error(f"Error creating {ITEM}: {e}", exc_info=True)

    async def update_sponsor(
        self,
        item_id: int,
        item: SponsorSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
