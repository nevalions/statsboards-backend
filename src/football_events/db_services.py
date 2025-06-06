from fastapi import HTTPException
from sqlalchemy import select

from src.core.models import BaseServiceDB, FootballEventDB

from ..logging_config import get_logger, setup_logging
from .schemas import FootballEventSchemaCreate, FootballEventSchemaUpdate

setup_logging()
ITEM = "FOOTBALL_EVENT"


class FootballEventServiceDB(BaseServiceDB):
    def __init__(
        self,
        database,
    ):
        super().__init__(database, FootballEventDB)
        self.logger = get_logger("backend_logger_FootballEventServiceDB", self)
        self.logger.debug("Initialized FootballEventServiceDB")

    async def create_match_football_event(
        self, football_event: FootballEventSchemaCreate
    ):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Creating {ITEM}")
                match_event = FootballEventDB(
                    match_id=football_event.match_id,
                    event_number=football_event.event_number,
                    event_qtr=football_event.event_qtr,
                    ball_on=football_event.ball_on,
                    ball_moved_to=football_event.ball_moved_to,
                    ball_picked_on=football_event.ball_picked_on,
                    ball_kicked_to=football_event.ball_kicked_to,
                    ball_returned_to=football_event.ball_returned_to,
                    ball_picked_on_fumble=football_event.ball_picked_on_fumble,
                    ball_returned_to_on_fumble=football_event.ball_returned_to_on_fumble,
                    offense_team=football_event.offense_team,
                    event_qb=football_event.event_qb,
                    event_down=football_event.event_down,
                    event_distance=football_event.event_distance,
                    distance_on_offence=football_event.distance_on_offence,
                    event_hash=football_event.event_hash,
                    play_direction=football_event.play_direction,
                    event_strong_side=football_event.event_strong_side,
                    play_type=football_event.play_type,
                    play_result=football_event.play_result,
                    score_result=football_event.score_result,
                    is_fumble=football_event.is_fumble,
                    is_fumble_recovered=football_event.is_fumble_recovered,
                    run_player=football_event.run_player,
                    pass_received_player=football_event.pass_received_player,
                    pass_dropped_player=football_event.pass_dropped_player,
                    pass_deflected_player=football_event.pass_deflected_player,
                    pass_intercepted_player=football_event.pass_intercepted_player,
                    fumble_player=football_event.fumble_player,
                    fumble_recovered_player=football_event.fumble_recovered_player,
                    tackle_player=football_event.tackle_player,
                    assist_tackle_player=football_event.assist_tackle_player,
                    sack_player=football_event.sack_player,
                    score_player=football_event.score_player,
                    defence_score_player=football_event.defence_score_player,
                    kickoff_player=football_event.kickoff_player,
                    return_player=football_event.return_player,
                    pat_one_player=football_event.pat_one_player,
                    flagged_player=football_event.flagged_player,
                    kick_player=football_event.kick_player,
                    punt_player=football_event.punt_player,
                )

                session.add(match_event)
                await session.commit()
                await session.refresh(match_event)
                if match_event:
                    self.logger.debug(f"{ITEM} created")
                    return match_event
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating {ITEM} "
                    f"for match id({football_event.match_id})"
                    f"returned some error",
                )
            except Exception as ex:
                self.logger.error(f"Error creating {ITEM} {ex}", exc_info=True)

    async def update_match_football_event(
        self,
        item_id: int,
        item: FootballEventSchemaUpdate,
        **kwargs,
    ):
        try:
            self.logger.debug(f"Updating {ITEM}")
            updated_ = await super().update(
                item_id,
                item,
                **kwargs,
            )

            return updated_
        except Exception as ex:
            self.logger.error(f"Error updating {ITEM} {ex}", exc_info=True)

    async def get_match_football_events_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Getting {ITEM}s by match id({match_id})")
                result = await session.scalars(
                    select(FootballEventDB).where(FootballEventDB.match_id == match_id)
                )
                if result:
                    match_events = result.all()
                    if match_events:
                        return match_events
                    else:
                        return []
            except Exception as ex:
                self.logger.error(
                    f"Error getting {ITEM}s with match id:{match_id} {ex}",
                    exc_info=True,
                )
