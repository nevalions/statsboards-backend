from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.decorators import handle_service_exceptions
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

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: FootballEventSchemaCreate) -> FootballEventDB:
        async with self.db.async_session() as session:
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
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=f"While creating {ITEM} for match id({item.match_id})returned some error",
            )

    @handle_service_exceptions(item_name=ITEM, operation="updating")
    async def update(
        self,
        item_id: int,
        item: FootballEventSchemaUpdate,
        **kwargs,
    ) -> FootballEventDB:
        self.logger.debug(f"Updating {ITEM}")
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )

        return updated_

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching match events", return_value_on_not_found=[]
    )
    async def get_match_football_events_by_match_id(self, match_id: int) -> list[FootballEventDB]:
        async with self.db.async_session() as session:
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

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching events with players", reraise_not_found=True
    )
    async def get_events_with_players(
        self,
        match_id: int,
    ) -> list[dict]:
        """
        Get all football events for a match with embedded player data.
        Single query with optimized joins using selectinload.
        """
        async with self.db.async_session() as session:
            self.logger.debug(f"Getting {ITEM}s with players for match id({match_id})")

            stmt = (
                select(FootballEventDB)
                .where(FootballEventDB.match_id == match_id)
                .order_by(FootballEventDB.event_number)
                .options(
                    selectinload(FootballEventDB.event_qb_rel),
                    selectinload(FootballEventDB.run_player_rel),
                    selectinload(FootballEventDB.pass_received_player_rel),
                    selectinload(FootballEventDB.pass_dropped_player_rel),
                    selectinload(FootballEventDB.pass_deflected_player_rel),
                    selectinload(FootballEventDB.pass_intercepted_player_rel),
                    selectinload(FootballEventDB.fumble_player_rel),
                    selectinload(FootballEventDB.fumble_recovered_player_rel),
                    selectinload(FootballEventDB.tackle_player_rel),
                    selectinload(FootballEventDB.assist_tackle_player_rel),
                    selectinload(FootballEventDB.sack_player_rel),
                    selectinload(FootballEventDB.score_player_rel),
                    selectinload(FootballEventDB.defence_score_player_rel),
                    selectinload(FootballEventDB.kick_player_rel),
                    selectinload(FootballEventDB.kickoff_player_rel),
                    selectinload(FootballEventDB.return_player_rel),
                    selectinload(FootballEventDB.pat_one_player_rel),
                    selectinload(FootballEventDB.flagged_player_rel),
                    selectinload(FootballEventDB.punt_player_rel),
                )
            )

            result = await session.execute(stmt)
            events = result.scalars().all()

            events_dict = []
            for event in events:
                event_data = {
                    "id": event.id,
                    "match_id": event.match_id,
                    "event_number": event.event_number,
                    "event_qtr": event.event_qtr,
                    "ball_on": event.ball_on,
                    "ball_moved_to": event.ball_moved_to,
                    "ball_picked_on": event.ball_picked_on,
                    "ball_kicked_to": event.ball_kicked_to,
                    "ball_returned_to": event.ball_returned_to,
                    "ball_picked_on_fumble": event.ball_picked_on_fumble,
                    "ball_returned_to_on_fumble": event.ball_returned_to_on_fumble,
                    "distance_on_offence": event.distance_on_offence,
                    "offense_team": event.offense_team,
                    "event_qb": event.event_qb,
                    "event_down": event.event_down,
                    "event_distance": event.event_distance,
                    "event_hash": event.event_hash,
                    "play_direction": event.play_direction,
                    "event_strong_side": event.event_strong_side,
                    "play_type": event.play_type,
                    "play_result": event.play_result,
                    "score_result": event.score_result,
                    "is_fumble": event.is_fumble,
                    "is_fumble_recovered": event.is_fumble_recovered,
                    "qb": self._player_match_to_dict(event.event_qb_rel),
                    "run_player": self._player_match_to_dict(event.run_player_rel),
                    "pass_received_player": self._player_match_to_dict(
                        event.pass_received_player_rel
                    ),
                    "pass_dropped_player": self._player_match_to_dict(
                        event.pass_dropped_player_rel
                    ),
                    "pass_deflected_player": self._player_match_to_dict(
                        event.pass_deflected_player_rel
                    ),
                    "pass_intercepted_player": self._player_match_to_dict(
                        event.pass_intercepted_player_rel
                    ),
                    "fumble_player": self._player_match_to_dict(event.fumble_player_rel),
                    "fumble_recovered_player": self._player_match_to_dict(
                        event.fumble_recovered_player_rel
                    ),
                    "tackle_player": self._player_match_to_dict(event.tackle_player_rel),
                    "assist_tackle_player": self._player_match_to_dict(
                        event.assist_tackle_player_rel
                    ),
                    "sack_player": self._player_match_to_dict(event.sack_player_rel),
                    "score_player": self._player_match_to_dict(event.score_player_rel),
                    "defence_score_player": self._player_match_to_dict(
                        event.defence_score_player_rel
                    ),
                    "kick_player": self._player_match_to_dict(event.kick_player_rel),
                    "kickoff_player": self._player_match_to_dict(event.kickoff_player_rel),
                    "return_player": self._player_match_to_dict(event.return_player_rel),
                    "pat_one_player": self._player_match_to_dict(event.pat_one_player_rel),
                    "flagged_player": self._player_match_to_dict(event.flagged_player_rel),
                    "punt_player": self._player_match_to_dict(event.punt_player_rel),
                }
                events_dict.append(event_data)

            self.logger.info(
                f"Retrieved {len(events_dict)} {ITEM}s with players for match {match_id}"
            )
            return events_dict

    def _player_match_to_dict(self, player_match) -> dict | None:
        """Helper to convert PlayerMatchDB to nested dict with full data."""
        if not player_match:
            return None

        player_data = None
        if (
            player_match.player_team_tournament
            and player_match.player_team_tournament.player
            and player_match.player_team_tournament.player.person
        ):
            player = player_match.player_team_tournament.player
            person = player.person
            player_data = {
                "id": player.id,
                "first_name": person.first_name,
                "second_name": person.second_name,
                "person_photo_url": person.person_photo_url,
            }

        position_data = None
        if player_match.match_position:
            position_data = {
                "id": player_match.match_position.id,
                "name": player_match.match_position.title,
            }

        team_data = None
        if player_match.team:
            team_data = {
                "id": player_match.team.id,
                "name": player_match.team.title,
                "logo_url": player_match.team.team_logo_url,
            }

        return {
            "id": player_match.id,
            "player_id": player_match.player_team_tournament_id,
            "player": player_data,
            "position": position_data,
            "team": team_data,
            "match_number": player_match.match_number,
        }
