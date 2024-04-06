from src.core.models import BaseServiceDB, SponsorLineDB
from .schemas import SponsorLineSchemaUpdate, SponsorLineSchemaCreate


class SponsorLineServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, SponsorLineDB)

    async def create_sponsor_line(
            self,
            sponsor_line: SponsorLineSchemaCreate,
    ):
        result = self.model(
            title=sponsor_line.title,
        )

        print('sponsor line', result)
        return await super().create(result)

    async def update_sponsor_line(
            self,
            item_id: int,
            item: SponsorLineSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
