from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.exceptions import NotFoundError
from src.core.models import BaseServiceDB, FootballEventDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import FootballEventSchemaCreate, FootballEventSchemaUpdate

ITEM = "FOOTBALL_EVENT"


class FootballEventServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, FootballEventDB)
        self.logger = get_logger("backend_logger_FootballEventServiceDB", self)
        self.logger.debug("Initialized FootballEventServiceDB")

    async def create(self, item: FootballEventSchemaCreate) -> FootballEventDB:
        async with self.db.async_session() as session:
            try:
                self.logger.debug(f"Creating {ITEM}")
                match_event = FootballEventDB(
                    match_id=item.match_id,
                    event_number=item.event_number,
                    event_qtr=item.event_qtr,
                    ball_on=item.ball_on,
                    ball_moved_to=item.ball_moved_to,
                    ball_picked_on=item.ball_picked_on,
                    ball_kicked_to=item.ball_kicked_to,
                    ball_returned_to=item.ball_returned_to,
                    ball_picked_on_fumble=item.ball_picked_on_fumble,
                    ball_returned_to_on_fumble=item.ball_returned_to_on_fumble,
                    offense_team=item.offense_team,
                    event_qb=item.event_qb,
                    event_down=item.event_down,
                    event_distance=item.event_distance,
                    distance_on_offence=item.distance_on_offence,
                    event_hash=item.event_hash,
                    play_direction=item.play_direction,
                    event_strong_side=item.event_strong_side,
                    play_type=item.play_type,
                    play_result=item.play_result,
                    score_result=item.score_result,
                    is_fumble=item.is_fumble,
                    is_fumble_recovered=item.is_fumble_recovered,
                    run_player=item.run_player,
                    pass_received_player=item.pass_received_player,
                    pass_dropped_player=item.pass_dropped_player,
                    pass_deflected_player=item.pass_deflected_player,
                    pass_intercepted_player=item.pass_intercepted_player,
                    fumble_player=item.fumble_player,
                    fumble_recovered_player=item.fumble_recovered_player,
                    tackle_player=item.tackle_player,
                    assist_tackle_player=item.assist_tackle_player,
                    sack_player=item.sack_player,
                    score_player=item.score_player,
                    defence_score_player=item.defence_score_player,
                    kickoff_player=item.kickoff_player,
                    return_player=item.return_player,
                    pat_one_player=item.pat_one_player,
                    flagged_player=item.flagged_player,
                    kick_player=item.kick_player,
                    punt_player=item.punt_player,
                )

                session.add(match_event)
                await session.commit()
                await session.refresh(match_event)
                if match_event:
                    self.logger.info(f"{ITEM} created")
                    return match_event
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating {ITEM} "
                    f"for match id({item.match_id})"
                    f"returned some error",
                )
            except HTTPException:
                await session.rollback()
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Database error creating {ITEM}: {ex}", exc_info=True
                )
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error creating football event for match {item.match_id}",
                )
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(f"Data error creating {ITEM}: {ex}", exc_info=True)
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="Invalid data provided for football event",
                )
            except NotFoundError as ex:
                self.logger.info(f"Not found creating {ITEM}: {ex}", exc_info=True)
                await session.rollback()
                raise HTTPException(status_code=404, detail=str(ex))
            except Exception as ex:
                self.logger.critical(f"Unexpected error creating {ITEM}: {ex}", exc_info=True)
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error creating football event",
                )

    async def update(
        self,
        item_id: int,
        item: FootballEventSchemaUpdate,
        **kwargs,
    ) -> FootballEventDB:
        try:
            self.logger.debug(f"Updating {ITEM}")
            updated_ = await super().update(
                item_id,
                item,
                **kwargs,
            )

            return updated_
        except HTTPException:
            raise
        except (IntegrityError, SQLAlchemyError) as ex:
            self.logger.error(f"Database error updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="Database error updating football event",
            )
        except (ValueError, KeyError, TypeError) as ex:
            self.logger.warning(f"Data error updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="Invalid data provided for football event",
            )
        except NotFoundError as ex:
            self.logger.info(f"Not found updating {ITEM}: {ex}", exc_info=True)
            raise HTTPException(status_code=404, detail=str(ex))
        except Exception as ex:
            self.logger.critical(f"Unexpected error updating {ITEM}: {ex}", exc_info=True)
            raise

    async def get_match_football_events_by_match_id(
        self, match_id: int
    ) -> list[FootballEventDB]:
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
                return []
            except HTTPException:
                await session.rollback()
                raise
            except (IntegrityError, SQLAlchemyError) as ex:
                self.logger.error(
                    f"Database error getting {ITEM}s with match id:{match_id} {ex}",
                    exc_info=True,
                )
                await session.rollback()
                return []
            except (ValueError, KeyError, TypeError) as ex:
                self.logger.warning(
                    f"Data error getting {ITEM}s with match id:{match_id} {ex}",
                    exc_info=True,
                )
                await session.rollback()
                return []
            except NotFoundError as ex:
                self.logger.info(
                    f"Not found {ITEM}s with match id:{match_id} {ex}",
                    exc_info=True,
                )
                await session.rollback()
                return []
            except Exception as ex:
                self.logger.critical(
                    f"Unexpected error getting {ITEM}s with match id:{match_id} {ex}",
                    exc_info=True,
                )
                await session.rollback()
                return []
