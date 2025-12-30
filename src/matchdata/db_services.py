from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.models.base import Database
from src.core.models import BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()
ITEM = "MATCHDATA"


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, MatchDataDB)
        # self.match_manager = MatchDataManager()
        self._running_tasks = {}
        self.logger = get_logger("backend_logger_MatchDataServiceDB", self)
        self.logger.debug(f"Initialized MatchDataServiceDB")

    async def create(self, item: MatchDataSchemaCreate) -> MatchDataDB:
        self.logger.debug(f"Creat {ITEM}:{item}")

        async with self.db.async_session() as session:
            try:
                match_data = MatchDataDB(
                    field_length=item.field_length,
                    game_status=item.game_status,
                    score_team_a=item.score_team_a,
                    score_team_b=item.score_team_b,
                    timeout_team_a=item.timeout_team_a,
                    timeout_team_b=item.timeout_team_b,
                    qtr=item.qtr,
                    ball_on=item.ball_on,
                    down=item.down,
                    distance=item.distance,
                    match_id=item.match_id,
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
                    f"for matchdata data({item})"
                    f"returned some error",
                )

    async def update(
        self,
        item_id: int,
        item: MatchDataSchemaUpdate,
        **kwargs,
    ) -> MatchDataDB:
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
        except HTTPException:
            raise
        except Exception as ex:
            self.logger.error(f"Error creating new match data: {ex}", exc_info=True)
            raise HTTPException(
                status_code=409,
                detail=f"Error creating new matchdata with data: {item}",
            )

    async def get_match_data_by_match_id(self, match_id: int) -> MatchDataDB | None:
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

    async def enable_match_data_clock_queues(
        self, match_data_id: int, clock_type: str
    ) -> None:
        self.logger.debug(
            f"Enable matchdata clock queues for id: {match_data_id}, type: {clock_type}"
        )
        await self.get_by_id(match_data_id)

    async def decrement_gameclock(
        self, background_tasks: BackgroundTasks, match_data_id: int
    ) -> None:
        self.logger.debug(f"Decrement gameclock for matchdata id: {match_data_id}")

    async def decrement_playclock(
        self, background_tasks: BackgroundTasks, match_data_id: int
    ) -> None:
        self.logger.debug(f"Decrement playclock for matchdata id: {match_data_id}")
