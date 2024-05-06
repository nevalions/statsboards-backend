from src.core.models import BaseServiceDB, PositionDB

from .schemas import PositionSchemaCreate, PositionSchemaUpdate


class PositionServiceDB(BaseServiceDB):
    def __init__(
            self,
            database,
    ):
        super().__init__(database, PositionDB)

    async def create_new_position(
            self,
            t: PositionSchemaCreate,
    ):
        position = self.model(
            sport_id=t.sport_id,
            title=t.title,
        )

        print('position', position)
        return await super().create(position)

    async def update_position(
            self,
            item_id: int,
            item: PositionSchemaUpdate,
            **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
