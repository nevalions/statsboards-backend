import asyncio
from typing import Union

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, ScoreboardDB, MatchDataDB
from .shemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()


class ScoreboardUpdateManager:
    def __init__(self):
        self.active_scoreboard_updates = {}
        self.logger = get_logger("backend_logger_ScoreboardUpdateManager", self)
        self.logger.debug(f"Initialized ScoreboardUpdateManager")

    async def enable_scoreboard_update_queue(self, scoreboard_id):
        if scoreboard_id not in self.active_scoreboard_updates:
            self.logger.debug(f"Queue not found for Scoreboard ID:{scoreboard_id}")
            self.active_scoreboard_updates[scoreboard_id] = asyncio.Queue()
            self.logger.debug(f"Queue added for Scoreboard ID:{scoreboard_id}")

    async def update_queue_scoreboard(self, scoreboard_id, updated_scoreboard):
        if scoreboard_id in self.active_scoreboard_updates:
            scoreboard_update_queue = self.active_scoreboard_updates[scoreboard_id]
            self.logger.debug(f"Queue updated for Scoreboard ID:{scoreboard_id}")
            await scoreboard_update_queue.put(updated_scoreboard)


class ScoreboardServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, ScoreboardDB)
        self.scoreboard_update_manager = ScoreboardUpdateManager()
        self.logger = get_logger("backend_logger_ScoreboardServiceDB", self)
        self.logger.debug(f"Initialized ScoreboardServiceDB")

    async def create_scoreboard(self, scoreboard: ScoreboardSchemaCreate):
        self.logger.debug(f"Create scoreboard: {scoreboard}")
        async with self.db.async_session() as session:
            try:
                scoreboard_result = ScoreboardDB(
                    is_qtr=scoreboard.is_qtr,
                    is_time=scoreboard.is_time,
                    is_playclock=scoreboard.is_playclock,
                    is_downdistance=scoreboard.is_downdistance,
                    is_tournament_logo=scoreboard.is_tournament_logo,
                    is_main_sponsor=scoreboard.is_main_sponsor,
                    is_sponsor_line=scoreboard.is_sponsor_line,
                    is_match_sponsor_line=scoreboard.is_match_sponsor_line,
                    is_team_a_start_offense=scoreboard.is_team_a_start_offense,
                    is_team_b_start_offense=scoreboard.is_team_b_start_offense,
                    is_team_a_start_defense=scoreboard.is_team_a_start_defense,
                    is_team_b_start_defense=scoreboard.is_team_b_start_defense,
                    is_home_match_team_lower=scoreboard.is_home_match_team_lower,
                    is_away_match_team_lower=scoreboard.is_away_match_team_lower,
                    is_football_qb_full_stats_lower=scoreboard.is_football_qb_full_stats_lower,
                    football_qb_full_stats_match_lower_id=scoreboard.football_qb_full_stats_match_lower_id,
                    is_match_player_lower=scoreboard.is_match_player_lower,
                    player_match_lower_id=scoreboard.player_match_lower_id,
                    team_a_game_color=scoreboard.team_a_game_color,
                    team_b_game_color=scoreboard.team_b_game_color,
                    team_a_game_title=scoreboard.team_a_game_title,
                    team_b_game_title=scoreboard.team_b_game_title,
                    team_a_game_logo=scoreboard.team_a_game_logo,
                    team_b_game_logo=scoreboard.team_b_game_logo,
                    use_team_a_game_color=scoreboard.use_team_a_game_color,
                    use_team_b_game_color=scoreboard.use_team_b_game_color,
                    use_team_a_game_title=scoreboard.use_team_a_game_title,
                    use_team_b_game_title=scoreboard.use_team_b_game_title,
                    use_team_a_game_logo=scoreboard.use_team_a_game_logo,
                    use_team_b_game_logo=scoreboard.use_team_b_game_logo,
                    scale_tournament_logo=scoreboard.scale_tournament_logo,
                    scale_main_sponsor=scoreboard.scale_main_sponsor,
                    scale_logo_a=scoreboard.scale_logo_a,
                    scale_logo_b=scoreboard.scale_logo_b,
                    is_flag=scoreboard.is_flag,
                    is_goal_team_a=scoreboard.is_goal_team_a,
                    is_goal_team_b=scoreboard.is_goal_team_b,
                    is_timeout_team_a=scoreboard.is_timeout_team_a,
                    is_timeout_team_b=scoreboard.is_timeout_team_b,
                    match_id=scoreboard.match_id,
                )

                self.logger.debug(f"Is scoreboard exist")
                is_exist = await self.get_scoreboard_by_match_id(scoreboard.match_id)
                if is_exist:
                    self.logger.info(f"Scoreboard already exists: {scoreboard_result}")
                    return scoreboard_result

                session.add(scoreboard_result)
                await session.commit()
                await session.refresh(scoreboard_result)

                self.logger.info(f"Scoreboard created: {scoreboard_result}")
                return scoreboard_result
            except Exception as ex:
                self.logger.error(
                    f"Error creating scoreboard with data: {scoreboard} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating playclock "
                    f"for match id({scoreboard.match_id})"
                    f"returned some error",
                )

            #     session.add(match_result)
            #     await session.commit()
            #     await session.refresh(match_result)
            #     return match_result
            # except Exception as ex:
            #     print(ex)
            #     raise HTTPException(
            #         status_code=409,
            #         detail=f"While creating result "
            #         f"for match id({scoreboard})"
            #         f"returned some error",
            #     )

    async def update_scoreboard(
        self,
        item_id: int,
        item: ScoreboardSchemaUpdate,
        **kwargs,
    ):
        self.logger.debug(f"Update scoreboard id:{item_id} data: {item}")
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        self.logger.debug(f"Updated scoreboard: {updated_}")
        # await self.trigger_update_scoreboard(item_id)
        return updated_

    async def get_scoreboard_by_match_id(
        self,
        value,
        field_name="match_id",
    ):
        self.logger.debug(f"Get scoreboard by {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def create_or_update_scoreboard(
        self,
        scoreboard: Union[ScoreboardSchemaCreate, ScoreboardSchemaUpdate],
    ):
        self.logger.debug(f"Create or update scoreboard: {scoreboard}")
        existing_scoreboard = await self.get_scoreboard_by_match_id(scoreboard.match_id)

        if existing_scoreboard:
            self.logger.info(f"Scoreboard already exists")
            if isinstance(scoreboard, ScoreboardSchemaUpdate):
                updated_scoreboard = await self.update_scoreboard(
                    existing_scoreboard.id, scoreboard
                )
                self.logger.debug(f"Updated scoreboard")
            else:
                self.logger.error(f"Wrong Schema for updating scoreboard")
                raise ValueError("Must use ScoreboardSchemaUpdate for updating.")
            return updated_scoreboard

        else:
            self.logger.debug(f"Scoreboard does not exist")
            if isinstance(scoreboard, ScoreboardSchemaCreate):
                new_scoreboard = await self.create_scoreboard(scoreboard)
                self.logger.info(f"Scoreboard created")
            else:
                self.logger.error(f"Wrong Schema for creating scoreboard")
                raise ValueError("Must use ScoreboardSchemaCreate for creating.")
            return new_scoreboard

    async def get_scoreboard_by_matchdata_id(
        self,
        matchdata_id,
    ):
        async with self.db.async_session() as session:
            self.logger.debug(f"Get scoreboard by matchdata id: {matchdata_id}")
            query = select(MatchDataDB).where(MatchDataDB.id == matchdata_id)
            result = await session.execute(query)
            matchdata = result.scalars().one_or_none()

            if matchdata is None:
                self.logger.warning(f"No matchdata found for id: {matchdata_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Match data with id {matchdata_id} not found",
                )
            try:
                self.logger.debug(f"Select scoreboard by matchdata id: {matchdata_id}")
                scoreboard_query = select(ScoreboardDB).where(
                    ScoreboardDB.match_id == matchdata.match_id
                )
                scoreboard_result = await session.execute(scoreboard_query)
                scoreboard = scoreboard_result.scalars().first()

                if scoreboard is None:
                    self.logger.warning(
                        f"No scoreboard found for matchdata id: {matchdata_id}"
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Scoreboard with match_id {matchdata.match_id} not found",
                    )
                return scoreboard
            except Exception as ex:
                self.logger.error(
                    f"Error getting scoreboard by matchdata id: {matchdata_id} {ex}",
                    exc_info=True,
                )

    """triggers for sse process, now we use websocket"""
    # async def event_generator_get_scoreboard_data(self, scoreboard_id: int):
    #     await self.scoreboard_update_manager.enable_scoreboard_update_queue(
    #         scoreboard_id
    #     )
    #     try:
    #         while (
    #             scoreboard_id
    #             in self.scoreboard_update_manager.active_scoreboard_updates
    #         ):
    #             print(f"Scoreboard {scoreboard_id} is active for updates")
    #
    #             update = await self.scoreboard_update_manager.active_scoreboard_updates[
    #                 scoreboard_id
    #             ].get()
    #
    #             update_data = self.to_dict(update)
    #
    #             data = {
    #                 "type": "scoreboardData",
    #                 "scoreboard_data": update_data,
    #             }
    #
    #             json_data = json.dumps(
    #                 data,
    #                 default=self.default_serializer,
    #             )
    #             yield f"data: {json_data}\n\n"
    #
    #         print(f"Scoreboard {scoreboard_id} stopped updates")
    #     except asyncio.CancelledError:
    #         pass
    #
    # async def trigger_update_scoreboard(self, scoreboard_id):
    #     # Fetch the latest store of the scoreboard
    #     scoreboard = await self.get_by_id(scoreboard_id)
    #
    #     # Ensure that the queue for this scoreboard is available
    #     if (
    #         scoreboard_id
    #         not in self.scoreboard_update_manager.active_scoreboard_updates
    #     ):
    #         print(f"Queue not found for Scoreboard ID:{scoreboard_id}")
    #         await self.scoreboard_update_manager.enable_scoreboard_update_queue(
    #             scoreboard_id
    #         )
    #     print("scoreboard triggered")
    #     # Trigger an update by adding the current scoreboard store to the queue
    #     await self.scoreboard_update_manager.update_queue_scoreboard(
    #         scoreboard_id,
    #         scoreboard,
    #     )
