import asyncio

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.models import BaseServiceDB, ScoreboardDB
from .shemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate


class ScoreboardServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, ScoreboardDB)

    async def create_scoreboard(self, scoreboard: ScoreboardSchemaCreate):
        async with self.db.async_session() as session:
            try:
                match_result = ScoreboardDB(
                    is_qtr=scoreboard.is_qtr,
                    is_time=scoreboard.is_time,
                    is_playclock=scoreboard.is_playclock,
                    is_downdistance=scoreboard.is_downdistance,
                    team_a_color=scoreboard.team_a_color,
                    team_b_color=scoreboard.team_b_color,
                    match_id=scoreboard.match_id,
                )

                session.add(match_result)
                await session.commit()
                await session.refresh(match_result)
                return match_result
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating result "
                    f"for match id({scoreboard})"
                    f"returned some error",
                )

    async def update_scoreboard(
        self,
        item_id: int,
        item: ScoreboardSchemaUpdate,
        **kwargs,
    ):
        return await super().update(
            item_id,
            item,
            **kwargs,
        )
