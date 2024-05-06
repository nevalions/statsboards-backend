from sqlalchemy import select, func

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
            title=t.title.upper(),
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

    async def get_position_by_title(self, title: str):
        async with self.db.async_session() as session:
            stmt = (
                select(PositionDB)
                .where(func.lower(func.trim(PositionDB.title)) == title.lower().strip())
            )
            results = await session.execute(stmt)
            position = results.scalars().one_or_none()
            return position
