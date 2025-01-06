from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "MATCHDATA"


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDataDB)
        # self.match_manager = MatchDataManager()
        self._running_tasks = {}
        self.logger = get_logger("backend_logger_MatchDataServiceDB", self)
        self.logger.debug(f"Initialized MatchDataServiceDB")

    async def create_match_data(self, matchdata: MatchDataSchemaCreate):
        self.logger.debug(f"Creat {ITEM}:{matchdata}")

        async with self.db.async_session() as session:
            try:
                match_data = MatchDataDB(
                    field_length=matchdata.field_length,
                    game_status=matchdata.game_status,
                    score_team_a=matchdata.score_team_a,
                    score_team_b=matchdata.score_team_b,
                    timeout_team_a=matchdata.timeout_team_a,
                    timeout_team_b=matchdata.timeout_team_b,
                    qtr=matchdata.qtr,
                    ball_on=matchdata.ball_on,
                    down=matchdata.down,
                    distance=matchdata.distance,
                    match_id=matchdata.match_id,
                )

                session.add(match_data)
                await session.commit()
                await session.refresh(match_data)

                self.logger.info(
                    f"Matchdata created successfully. Result: {match_data}"
                )
                return match_data
            except Exception as ex:
                self.logger.error(
                    f"Error creating new match data({match_data}): {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating result "
                    f"for matchdata data({matchdata})"
                    f"returned some error",
                )

    async def update_match_data(
        self,
        item_id: int,
        item: MatchDataSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(
            f"Update matchdata with item_id: {item_id}, new matchdata: {item}"
        )

        try:
            updated_ = await super().update(
                item_id,
                item,
                **kwargs,
            )
            """triggers for sse process, now we use websocket
            await self.trigger_update_match_data(item_id)"""
            # await self.trigger_update_match_data(item_id)
            self.logger.info(
                f"Matchdata updated  successfully. Updated: {updated_.__dict__}"
            )
            return updated_
        except Exception as ex:
            self.logger.error(f"Error creating new match data: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating new matchdata with data: {item}",
            )

    async def get_match_data_by_match_id(self, match_id: int):
        self.logger.debug(f"Get {ITEM} by match id: {match_id}")

        async with self.db.async_session() as session:
            try:
                result = await session.scalars(
                    select(MatchDataDB).where(MatchDataDB.match_id == match_id)
                )
                if result:
                    self.logger.debug(
                        f"get_match_data_by_match_id completed successfully."
                    )
                    return result.one_or_none()
                else:
                    self.logger.debug(
                        f"No matchdata in match with match_id: {match_id}"
                    )
                    return None
            except Exception as ex:
                self.logger.error(
                    f"Error getting {ITEM} with match id:{match_id} {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Error creating new matchdata with match id: {match_id}",
                )
