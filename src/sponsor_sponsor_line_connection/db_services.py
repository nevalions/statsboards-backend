from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import (
    BaseServiceDB,
    SponsorSponsorLineDB,
    SponsorDB,
    SponsorLineDB,
)
from .schemas import SponsorSponsorLineSchemaCreate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "SPONSOR_SPONSOR_LINE"


class SponsorSponsorLineServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, SponsorSponsorLineDB)
        self.logger = get_logger("backend_logger_SponsorSponsorLineServiceDB", self)
        self.logger.debug(f"Initialized SponsorSponsorLineServiceDB")

    async def create_sponsor_sponsor_line_relation(
        self,
        sponsor_sponsor_line: SponsorSponsorLineSchemaCreate,
    ):
        try:
            self.logger.debug(f"Creating {ITEM}")
            is_relation_exist = await self.get_sponsor_sponsor_line_relation(
                sponsor_sponsor_line.sponsor_line_id,
                sponsor_sponsor_line.sponsor_id,
            )
            if is_relation_exist:
                self.logger.debug(f"Relation {ITEM} already exists")
                return is_relation_exist
            new_sponsor_sponsor_line = self.model(
                sponsor_line_id=sponsor_sponsor_line.sponsor_line_id,
                sponsor_id=sponsor_sponsor_line.sponsor_id,
                position=sponsor_sponsor_line.position,
            )
            return await super().create(new_sponsor_sponsor_line)
        except Exception as e:
            self.logger.error(f"Error creating {ITEM}: {e}", exc_info=True)

    async def get_sponsor_sponsor_line_relation(
        self, sponsor_id: int, sponsor_line_id: int
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Getting {ITEM}")
                result = await session.execute(
                    select(SponsorSponsorLineDB).where(
                        (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                        & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                    )
                )
                sponsor_sponsor_line = result.scalars().first()
                await session.commit()
                return sponsor_sponsor_line
            except Exception as e:
                self.logger.error(f"Error getting {ITEM}: {e}", exc_info=True)

    async def get_related_sponsors(self, sponsor_line_id: int):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(
                    f"Getting sponsors by sponsor line id: {sponsor_line_id}"
                )
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
                await session.commit()
                return {"sponsor_line": sponsor_line, "sponsors": sponsors}
            except Exception as e:
                self.logger.error(
                    f"Error getting related sponsors by sponsor line id:{sponsor_line_id}: {e}",
                    exc_info=True,
                )

    async def delete_relation_by_sponsor_and_sponsor_line_id(
        self, sponsor_id: int, sponsor_line_id: int
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Deleting {ITEM}")
                result = await session.execute(
                    select(SponsorSponsorLineDB).where(
                        (SponsorSponsorLineDB.sponsor_id == sponsor_id)
                        & (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                    )
                )

                item = result.scalars().first()

                if not item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Connection sponsor id: {sponsor_id} and sponsor_line id {sponsor_line_id} not found",
                    )

                await session.delete(item)
                await session.commit()
                raise HTTPException(
                    status_code=200,
                    detail=f"Connection sponsor id: {sponsor_id} and sponsor_line id {sponsor_line_id} deleted",
                )
            except Exception as e:
                self.logger.error(f"Error deleting {ITEM}: {e}", exc_info=True)
