from src.core.models import db, BaseServiceDB, SponsorDB
from src.sponsors.schemas import SponsorSchemaUpdate, SponsorSchemaCreate


class SponsorServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, SponsorDB)

    async def create_sponsor(
            self,
            t: SponsorSchemaCreate,
    ):
        sponsor = self.model(
            title=t.title,
            logo_url=t.logo_url,
            scale_logo=t.scale_logo,
        )

        print('sponsor', sponsor)
        return await super().create(sponsor)

    async def update_sponsor(
            self,
            item_id: int,
            item: SponsorSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
