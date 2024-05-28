import asyncio
import json
from typing import Union

from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, ScoreboardDB, MatchDataDB
from .shemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate


class ScoreboardUpdateManager:
    def __init__(self):
        self.active_scoreboard_updates = {}

    async def enable_scoreboard_update_queue(self, scoreboard_id):
        if scoreboard_id not in self.active_scoreboard_updates:
            print(f"Queue not found for Scoreboard ID:{scoreboard_id}")
            self.active_scoreboard_updates[scoreboard_id] = asyncio.Queue()
            print(f"Queue added for Scoreboard ID:{scoreboard_id}")

    async def update_queue_scoreboard(self, scoreboard_id, updated_scoreboard):
        if scoreboard_id in self.active_scoreboard_updates:
            scoreboard_update_queue = self.active_scoreboard_updates[scoreboard_id]
            await scoreboard_update_queue.put(updated_scoreboard)


class ScoreboardServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, ScoreboardDB)
        self.scoreboard_update_manager = ScoreboardUpdateManager()

    async def create_scoreboard(self, scoreboard: ScoreboardSchemaCreate):
        async with self.db.async_session() as session:
            try:
                match_result = ScoreboardDB(
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
        # print(item)
        updated_item = await super().update(
            item_id,
            item,
            **kwargs,
        )
        print("scoreboard updated", updated_item)
        await self.trigger_update_scoreboard(item_id)
        return updated_item

    async def get_scoreboard_by_match_id(
        self,
        value,
        field_name="match_id",
    ):
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def create_or_update_scoreboard(
        self,
        scoreboard: Union[ScoreboardSchemaCreate, ScoreboardSchemaUpdate],
    ):
        existing_scoreboard = await self.get_scoreboard_by_match_id(scoreboard.match_id)

        if existing_scoreboard:
            if isinstance(scoreboard, ScoreboardSchemaUpdate):
                updated_scoreboard = await self.update_scoreboard(
                    existing_scoreboard.id, scoreboard
                )
            else:
                raise ValueError("Must use ScoreboardSchemaUpdate for updating.")
            return updated_scoreboard

        else:
            if isinstance(scoreboard, ScoreboardSchemaCreate):
                new_scoreboard = await self.create_scoreboard(scoreboard)
            else:
                raise ValueError("Must use ScoreboardSchemaCreate for creating.")
            return new_scoreboard

    async def get_scoreboard_by_matchdata_id(
        self,
        matchdata_id,
    ):
        async with self.db.async_session() as session:
            query = select(MatchDataDB).where(MatchDataDB.id == matchdata_id)
            result = await session.execute(query)
            matchdata = result.scalars().one_or_none()

            if matchdata is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match data with id {matchdata_id} not found",
                )

            scoreboard_query = select(ScoreboardDB).where(
                ScoreboardDB.match_id == matchdata.match_id
            )
            scoreboard_result = await session.execute(scoreboard_query)
            scoreboard = scoreboard_result.scalars().first()

            if scoreboard is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Scoreboard with match_id {matchdata.match_id} not found",
                )

            return scoreboard

    async def event_generator_get_scoreboard_data(self, scoreboard_id: int):
        await self.scoreboard_update_manager.enable_scoreboard_update_queue(
            scoreboard_id
        )
        try:
            while (
                scoreboard_id
                in self.scoreboard_update_manager.active_scoreboard_updates
            ):
                print(f"Scoreboard {scoreboard_id} is active for updates")

                update = await self.scoreboard_update_manager.active_scoreboard_updates[
                    scoreboard_id
                ].get()

                update_data = self.to_dict(update)

                data = {
                    "type": "scoreboardData",
                    "scoreboard_data": update_data,
                }

                json_data = json.dumps(
                    data,
                    default=self.default_serializer,
                )
                yield f"data: {json_data}\n\n"

            print(f"Scoreboard {scoreboard_id} stopped updates")
        except asyncio.CancelledError:
            pass

    async def trigger_update_scoreboard(self, scoreboard_id):
        # Fetch the latest store of the scoreboard
        scoreboard = await self.get_by_id(scoreboard_id)

        # Ensure that the queue for this scoreboard is available
        if (
            scoreboard_id
            not in self.scoreboard_update_manager.active_scoreboard_updates
        ):
            print(f"Queue not found for Scoreboard ID:{scoreboard_id}")
            await self.scoreboard_update_manager.enable_scoreboard_update_queue(
                scoreboard_id
            )
        print("scoreboard triggered")
        # Trigger an update by adding the current scoreboard store to the queue
        await self.scoreboard_update_manager.update_queue_scoreboard(
            scoreboard_id,
            scoreboard,
        )
