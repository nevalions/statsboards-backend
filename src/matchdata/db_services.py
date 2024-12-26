import asyncio
import json
import logging

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, MatchDataDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from ..logging_config import setup_logging

setup_logging()
logger = logging.getLogger("backend_logger_MatchDataServiceDB")


class MatchDataManager:
    def __init__(self):
        self.active_matchdata_updates = {}

    async def enable_match_data_update_queue(self, match_data_id):
        if match_data_id not in self.active_matchdata_updates:
            self.active_matchdata_updates[match_data_id] = asyncio.Queue()

    async def update_queue_match_data(self, match_data_id, updated_match_data):
        print(f"Updating {match_data_id} in set")
        if match_data_id in self.active_matchdata_updates:
            matchdata_update_queue = self.active_matchdata_updates[match_data_id]
            await matchdata_update_queue.put(updated_match_data)
            print(f"Updated {match_data_id} in set")
        print(f"Finished Updating")


# class MatchDataServiceDB(BaseServiceDB):
#     def __init__(self, database):
#         super().__init__(database, MatchDataDB)
#         self.match_manager = MatchDataManager()
#         self._running_tasks = {}
#
#     async def create_match_data(self, matchdata: MatchDataSchemaCreate):
#         async with self.db.async_session() as session:
#             try:
#                 match_result = MatchDataDB(
#                     field_length=matchdata.field_length,
#                     game_status=matchdata.game_status,
#                     score_team_a=matchdata.score_team_a,
#                     score_team_b=matchdata.score_team_b,
#                     timeout_team_a=matchdata.timeout_team_a,
#                     timeout_team_b=matchdata.timeout_team_b,
#                     qtr=matchdata.qtr,
#                     ball_on=matchdata.ball_on,
#                     down=matchdata.down,
#                     distance=matchdata.distance,
#                     match_id=matchdata.match_id,
#                 )
#
#                 session.add(match_result)
#                 await session.commit()
#                 await session.refresh(match_result)
#
#                 return match_result
#             except Exception as ex:
#                 print(ex)
#                 raise HTTPException(
#                     status_code=409,
#                     detail=f"While creating result "
#                     f"for match id({matchdata.id})"
#                     f"returned some error",
#                 )
#
#     async def update_match_data(
#         self,
#         item_id: int,
#         item: MatchDataSchemaUpdate,
#         **kwargs,
#     ):
#         updated_ = await super().update(
#             item_id,
#             item,
#             **kwargs,
#         )
#         await self.trigger_update_match_data(item_id)
#         print(updated_.__dict__)
#         return updated_
#
#     async def get_match_data_by_match_id(self, match_id: int):
#         async with self.db.async_session() as session:
#             result = await session.scalars(
#                 select(MatchDataDB).where(MatchDataDB.match_id == match_id)
#             )
#             if result:
#                 print(result.__dict__)
#                 match_data = result.one_or_none()
#                 if match_data:
#                     return match_data


class MatchDataServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, MatchDataDB)
        self.match_manager = MatchDataManager()
        self._running_tasks = {}

    async def create_match_data(self, matchdata: MatchDataSchemaCreate):
        logger.debug(f"create_match_data called with matchdata: {matchdata}")

        async with self.db.async_session() as session:
            try:
                match_result = MatchDataDB(
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

                session.add(match_result)
                await session.commit()
                await session.refresh(match_result)

                logger.debug(
                    f"create_match_data completed successfully. Result: {match_result}"
                )
                return match_result
            except Exception as ex:
                logger.error(f"Error in create_match_data: {ex}")
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating result "
                    f"for match id({matchdata.id})"
                    f"returned some error",
                )

    async def update_match_data(
        self,
        item_id: int,
        item: MatchDataSchemaUpdate,
        **kwargs,
    ):
        logger.debug(f"update_match_data called with item_id: {item_id}, item: {item}")

        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        await self.trigger_update_match_data(item_id)
        logger.debug(
            f"update_match_data completed successfully. Updated: {updated_.__dict__}"
        )
        return updated_

    async def get_match_data_by_match_id(self, match_id: int):
        logger.debug(f"get_match_data_by_match_id called with match_id: {match_id}")

        async with self.db.async_session() as session:
            result = await session.scalars(
                select(MatchDataDB).where(MatchDataDB.match_id == match_id)
            )
            if result:
                logger.debug(
                    f"get_match_data_by_match_id completed successfully. Result: {result.one_or_none().__dict__}"
                )
                return result.one_or_none()
            else:
                logger.debug(
                    f"get_match_data_by_match_id completed with no result for match_id: {match_id}"
                )
                return None

    async def trigger_update_match_data(self, match_data_id):
        match_data = await self.get_by_id(match_data_id)
        print(match_data)
        if match_data_id not in self.match_manager.active_matchdata_updates:
            print(f"Queue not found for MatchData ID:{match_data_id}")
            await self.match_manager.enable_match_data_update_queue(match_data_id)

        await self.match_manager.update_queue_match_data(match_data_id, match_data)

    async def event_generator_get_match_data(self, match_data_id: int):
        await self.match_manager.enable_match_data_update_queue(match_data_id)
        try:
            while match_data_id in self.match_manager.active_matchdata_updates:
                print(f"Match {match_data_id} is active for updates")
                message = await self.match_manager.active_matchdata_updates[
                    match_data_id
                ].get()
                message_dict = self.to_dict(message)

                # Create a new dictionary with 'type' and 'data' properties
                data = {
                    "type": "matchData",
                    "data": message_dict,
                }

                json_data = json.dumps(
                    data,
                    default=self.default_serializer,
                )
                print(f"Match data {json_data} sent")
                yield f"data: {json_data}\n\n"

            print(f"Match data {match_data_id} stopped updates")
        except asyncio.CancelledError:
            print("Cancelled")
            pass
