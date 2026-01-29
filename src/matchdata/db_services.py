from fastapi import BackgroundTasks
from sqlalchemy import select

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, MatchDataDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate

ITEM = "MATCHDATA"


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, MatchDataDB)
        # self.match_manager = MatchDataManager()
        self._running_tasks = {}
        self.logger = get_logger("MatchDataServiceDB", self)
        self.logger.debug("Initialized MatchDataServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: MatchDataSchemaCreate) -> MatchDataDB:
        self.logger.debug(f"Creat {ITEM}:{item}")
        result = await super().create(item)
        return result  # type: ignore

    @handle_service_exceptions(item_name=ITEM, operation="updating", return_value_on_not_found=None)
    async def update(
        self,
        item_id: int,
        item: MatchDataSchemaUpdate,
        **kwargs,
    ) -> MatchDataDB | None:
        self.logger.debug(f"Updating matchdata item_id: {item_id}")

        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        if updated_ is None:
            return None
        """triggers for sse process, now we use websocket
        await self.trigger_update_match_data(item_id)"""
        # await self.trigger_update_match_data(item_id)
        self.logger.info(f"Matchdata updated  successfully. Updated: {updated_.__dict__}")
        return updated_

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching by match id", return_value_on_not_found=None
    )
    async def get_match_data_by_match_id(self, match_id: int) -> MatchDataDB | None:
        self.logger.debug(f"Get {ITEM} by match id: {match_id}")

        async with self.db.get_session_maker()() as session:
            result = await session.scalars(
                select(MatchDataDB).where(MatchDataDB.match_id == match_id)
            )
            if result:
                self.logger.debug("get_match_data_by_match_id completed successfully.")
                return result.one_or_none()
            else:
                self.logger.debug(f"No matchdata in match with match_id: {match_id}")
                return None

    async def enable_match_data_clock_queues(self, match_data_id: int, clock_type: str) -> None:
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
