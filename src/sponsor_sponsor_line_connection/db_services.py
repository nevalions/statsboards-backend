from sqlalchemy import select

from src.core.decorators import handle_service_exceptions
from src.core.exceptions import NotFoundError
from src.core.models import (
    BaseServiceDB,
    SponsorDB,
    SponsorLineDB,
    SponsorSponsorLineDB,
)
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import SponsorSponsorLineSchemaCreate

ITEM = "SPONSOR_SPONSOR_LINE"


class SponsorSponsorLineServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, SponsorSponsorLineDB)
        self.logger = get_logger("backend_logger_SponsorSponsorLineServiceDB", self)
        self.logger.debug("Initialized SponsorSponsorLineServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating", return_value_on_not_found=None)
    async def create(
        self,
        item: SponsorSponsorLineSchemaCreate,
    ) -> SponsorSponsorLineDB | None:
        self.logger.debug(f"Creating {ITEM}")
        is_relation_exist = await self.get_sponsor_sponsor_line_relation(
            item.sponsor_id,
            item.sponsor_line_id,
        )
        if is_relation_exist:
            self.logger.debug(f"Relation {ITEM} already exists")
            return None
        return await super().create(item)

    @handle_service_exceptions(item_name=ITEM, operation="fetching", return_value_on_not_found=None)
    async def get_sponsor_sponsor_line_relation(
        self, sponsor_id: int, sponsor_line_id: int
    ) -> SponsorSponsorLineDB | None:
        self.logger.debug(f"Getting {ITEM}")
        async with self.db.async_session() as session:
            result = await session.execute(
                select(SponsorSponsorLineDB).where(
                    (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                    & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                )
            )
            sponsor_sponsor_line = result.scalars().first()
            return sponsor_sponsor_line

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching related sponsors",
        return_value_on_not_found={"sponsor_line": None, "sponsors": []},
    )
    async def get_related_sponsors(self, sponsor_line_id: int) -> dict:
        self.logger.debug(f"Getting sponsors by sponsor line id: {sponsor_line_id}")
        async with self.db.async_session() as session:
            sponsor_line = await session.get(SponsorLineDB, sponsor_line_id)
            result = await session.execute(
                select(SponsorDB, SponsorSponsorLineDB.position)
                .join(
                    SponsorSponsorLineDB,
                    SponsorDB.id == SponsorSponsorLineDB.sponsor_id,
                )
                .where(SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
            )
            sponsors = [{"sponsor": r[0], "position": r[1]} for r in result.all()]
            return {"sponsor_line": sponsor_line, "sponsors": sponsors}

    @handle_service_exceptions(item_name=ITEM, operation="deleting", reraise_not_found=True)
    async def delete_relation_by_sponsor_and_sponsor_line_id(
        self, sponsor_id: int, sponsor_line_id: int
    ) -> SponsorSponsorLineDB:
        self.logger.debug(f"Deleting {ITEM}")
        async with self.db.async_session() as session:
            result = await session.execute(
                select(SponsorSponsorLineDB).where(
                    (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                    & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                )
            )

            item = result.scalars().first()

            if not item:
                raise NotFoundError(
                    f"Connection sponsor id: {sponsor_id} and sponsor line id {sponsor_line_id} not found"
                )

            await session.delete(item)
            await session.commit()
            self.logger.info(
                f"Deleted {ITEM}: sponsor_id={sponsor_id}, sponsor_line_id={sponsor_line_id}"
            )
            return item
