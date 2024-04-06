from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, SponsorSponsorLineDB, SponsorDB
from .schemas import SponsorSponsorLineSchemaCreate


class SponsorSponsorLineServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, SponsorSponsorLineDB)

    async def create_sponsor_sponsor_line_relation(
            self,
            sponsor_sponsor_line: SponsorSponsorLineSchemaCreate,
    ):
        is_relation_exist = await self.get_sponsor_sponsor_line_relation(
            sponsor_sponsor_line.sponsor_line_id,
            sponsor_sponsor_line.sponsor_id, )
        if is_relation_exist:
            return is_relation_exist
        new_sponsor_sponsor_line = self.model(
            sponsor_line_id=sponsor_sponsor_line.sponsor_line_id,
            sponsor_id=sponsor_sponsor_line.sponsor_id,
        )
        return await super().create(new_sponsor_sponsor_line)

    async def get_sponsor_sponsor_line_relation(self, sponsor_id: int, sponsor_line_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(SponsorSponsorLineDB).where(
                    (SponsorSponsorLineDB.sponsor_id == sponsor_id) &
                    (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                )
            )
            sponsor_sponsor_line = result.scalars().first()
            await session.commit()
        return sponsor_sponsor_line

    async def get_related_sponsors(self, sponsor_line_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(SponsorDB).join(SponsorSponsorLineDB).where(
                    SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id
                )
            )
            teams = result.scalars().all()
            await session.commit()
            return teams

    async def delete_relation_by_sponsor_and_sponsor_line_id(self, sponsor_id: int, sponsor_line_id: int):
        async with self.db.async_session() as session:
            result = await session.execute(
                select(SponsorSponsorLineDB).where(
                    (SponsorSponsorLineDB.sponsor_id == sponsor_id) &
                    (SponsorSponsorLineDB.sponsor_line_id == sponsor_line_id)
                )
            )

            item = result.scalars().first()

            if not item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Connection team id: {sponsor_id} and tournament id {sponsor_line_id} not foutnd"
                )

            await session.delete(item)
            await session.commit()
            raise HTTPException(
                status_code=200,
                detail=f"Connection team id: {sponsor_id} and tournament id {sponsor_line_id} deleted",
            )
