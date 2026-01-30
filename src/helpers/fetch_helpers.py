import asyncio
import datetime
import time
from typing import Any

from fastapi import status
from sqlalchemy import select

from src.core import db
from src.core.models import TeamDB
from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate
from src.logging_config import get_logger
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.schemas import ScoreboardSchemaCreate
from src.tournaments.db_services import TournamentServiceDB

logger = get_logger("helpers")
fetch_data_logger = get_logger("fetch_data")


async def fetch_list_of_matches_data(matches: list[Any]) -> list[dict[str, Any]] | None:
    fetch_data_logger.debug("Fetching list of matches data")
    from src.matches.db_services import MatchServiceDB

    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)
    all_match_data = []

    try:
        if not matches:
            return []

        match_ids = [match.id for match in matches]

        team_ids = set()
        for match in matches:
            team_ids.add(match.team_a_id)
            team_ids.add(match.team_b_id)

        async with db.async_session() as session:
            stmt = select(TeamDB).where(TeamDB.id.in_(list(team_ids)))
            results = await session.execute(stmt)
            teams = {team.id: team for team in results.scalars().all()}

        match_data_list = await asyncio.gather(
            *[match_service_db.get_matchdata_by_match(match_id) for match_id in match_ids]
        )

        for idx, match in enumerate(matches):
            match_id = match.id
            match_data = match_data_list[idx]
            team_a = teams.get(match.team_a_id)
            team_b = teams.get(match.team_b_id)

            match_teams_data = {"team_a": team_a, "team_b": team_b}

            if match_data is None:
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                match_data = await match_data_service_db.create(match_data_schema)

            all_match_data.append(
                {
                    "match_id": match_id,
                    "id": match_id,
                    "status_code": status.HTTP_200_OK,
                    "match": match,
                    "teams_data": match_teams_data,
                    "match_data": match_data.__dict__,
                }
            )

        return all_match_data
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching list of matches data: {e}", exc_info=True)


async def fetch_match_data(match_id: int, database=None) -> dict[str, Any] | None:
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Fetching matchdata by mathc_id:{match_id}")
    try:
        _db = database or db
        match_data_service_db = MatchDataServiceDB(_db)
        match_service_db = MatchServiceDB(_db)

        match, match_teams_data, match_data = await asyncio.gather(
            match_service_db.get_by_id(match_id),
            match_service_db.get_teams_by_match(match_id),
            match_service_db.get_matchdata_by_match(match_id),
        )

        if match:
            if match_data is None:
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                match_data = await match_data_service_db.create(match_data_schema)

            return {
                "match_id": match_id,
                "id": match_id,
                "status_code": status.HTTP_200_OK,
                "match": match,
                "teams_data": match_teams_data,
                "match_data": match_data.__dict__,
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching matchdata: {e}", exc_info=True)


async def fetch_with_scoreboard_data(
    match_id: int, database=None, cache_service=None
) -> dict[str, Any] | None:
    if cache_service:
        result = await cache_service.get_or_fetch_match_data(match_id)
        if result:
            return result

    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching match data with match_id {match_id}")
    _db = database or db
    scoreboard_data_service = ScoreboardServiceDB(_db)
    match_data_service_db = MatchDataServiceDB(_db)
    match_service_db = MatchServiceDB(_db)

    try:
        (
            scoreboard_data,
            match,
            match_teams_data,
            match_data,
            players,
            events,
        ) = await asyncio.gather(
            match_service_db.get_scoreboard_by_match(match_id),
            match_service_db.get_match_with_tournament_sponsor(match_id),
            match_service_db.get_teams_by_match(match_id),
            match_service_db.get_matchdata_by_match(match_id),
            match_service_db.get_players_with_full_data_optimized(match_id),
            _fetch_events_by_match(match_id, database=_db),
        )
        fetch_data_logger.debug(f"Fetched scoreboard for match_id: {match_id}")
        fetch_data_logger.debug(f"Fetched match for match_id: {match_id}")
        fetch_data_logger.debug(f"Fetched match_data for match_id: {match_id}")

        if match:
            if match_data is None:
                fetch_data_logger.debug(
                    f"Match Data not found for match_id:{match_id}, creating new..."
                )
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                fetch_data_logger.debug(f"Schema for match data {match_data_schema}")
                match_data = await match_data_service_db.create(match_data_schema)
            if scoreboard_data is None:
                fetch_data_logger.debug(
                    f"Scoreboard Data not found for match_id:{match_id}, creating new..."
                )
                scoreboard_data_schema = ScoreboardSchemaCreate(match_id=match_id)
                fetch_data_logger.debug(f"Schema for scoreboard data {scoreboard_data_schema}")
                scoreboard_data = await scoreboard_data_service.create(scoreboard_data_schema)

            # Convert match to dict and rename 'tournaments' to 'tournament' for frontend compatibility
            match_dict = deep_dict_convert(match.__dict__)
            if match_dict and "tournaments" in match_dict:
                match_dict["tournament"] = match_dict.pop("tournaments")

            final_match_with_scoreboard_data_fetched = {
                "data": {
                    "match_id": match_id,
                    "id": match_id,
                    "status_code": status.HTTP_200_OK,
                    "match": match_dict,
                    "scoreboard_data": instance_to_dict(dict(scoreboard_data.__dict__)),
                    "teams_data": deep_dict_convert(match_teams_data),
                    "match_data": instance_to_dict(dict(match_data.__dict__)),
                    "players": [deep_dict_convert(player) for player in players] if players else [],
                    "events": [deep_dict_convert(event.__dict__) for event in events]
                    if events
                    else [],
                }
            }
            match_id = final_match_with_scoreboard_data_fetched.get("data", {}).get(
                "match_id", "N/A"
            )
            num_players = len(
                final_match_with_scoreboard_data_fetched.get("data", {}).get("players", [])
            )
            num_events = len(
                final_match_with_scoreboard_data_fetched.get("data", {}).get("events", [])
            )
            fetch_data_logger.debug(
                f"Final match with scoreboard fetched for match_id: {match_id}, "
                f"players: {num_players}, events: {num_events}"
            )

            return final_match_with_scoreboard_data_fetched
        else:
            fetch_data_logger.error(f"Match not found for match_id:{match_id}")
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(
            f"Error while fetching matchdata with scoreboard: {e}", exc_info=True
        )
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


async def fetch_gameclock(
    match_id: int, database=None, cache_service=None
) -> dict[str, Any] | None:
    if cache_service:
        result = await cache_service.get_or_fetch_gameclock(match_id)
        if result:
            return result

    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching gemeclock with match_id:{match_id}")
    _db = database or db
    gameclock_service = GameClockServiceDB(_db)
    match_service_db = MatchServiceDB(_db)

    try:
        match, gameclock = await asyncio.gather(
            match_service_db.get_by_id(match_id),
            gameclock_service.get_gameclock_by_match_id(match_id),
        )

        if match:
            if gameclock is None:
                gameclock_schema = GameClockSchemaCreate(match_id=match_id)
                gameclock = await gameclock_service.create(gameclock_schema)
            return {
                "match_id": match_id,
                "gameclock": instance_to_dict(dict(gameclock.__dict__)),
                "server_time_ms": int(time.time() * 1000),
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching gameclock: {e}", exc_info=True)
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


async def fetch_playclock(
    match_id: int, database=None, cache_service=None
) -> dict[str, Any] | None:
    if cache_service:
        result = await cache_service.get_or_fetch_playclock(match_id)
        if result:
            return result

    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching playclock with match_id:{match_id}")
    _db = database or db
    playclock_service = PlayClockServiceDB(_db)
    match_service_db = MatchServiceDB(_db)
    try:
        match, playclock = await asyncio.gather(
            match_service_db.get_by_id(match_id),
            playclock_service.get_playclock_by_match_id(match_id),
        )

        if match:
            if playclock is None:
                playclock_schema = PlayClockSchemaCreate(match_id=match_id)
                playclock = await playclock_service.create(playclock_schema)
            return {
                "match_id": match_id,
                "playclock": instance_to_dict(dict(playclock.__dict__)),
                "server_time_ms": int(time.time() * 1000),
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching playclock: {e}", exc_info=True)
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


async def fetch_event(event_id: int, database=None, cache_service=None) -> dict[str, Any] | None:
    if cache_service:
        result = await cache_service.get_or_fetch_event_data(event_id)
        if result:
            return result

    from src.football_events.db_services import FootballEventServiceDB
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching event with event_id:{event_id}")
    _db = database or db
    football_event_service = FootballEventServiceDB(_db)
    match_service_db = MatchServiceDB(_db)

    try:
        match = await match_service_db.get_by_id(event_id)

        if match:
            event_data_list = await football_event_service.get_events_with_players(event_id)
            return {
                "match_id": event_id,
                "id": event_id,
                "status_code": status.HTTP_200_OK,
                "events": event_data_list,
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching event: {e}", exc_info=True)
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


async def fetch_stats(match_id: int, database=None, cache_service=None) -> dict[str, Any] | None:
    if cache_service:
        result = await cache_service.get_or_fetch_stats(match_id)
        if result:
            return result

    from src.matches.stats_service import MatchStatsServiceDB

    fetch_data_logger.debug(f"Starting fetching stats with match_id:{match_id}")
    _db = database or db
    stats_service = MatchStatsServiceDB(_db)

    try:
        stats = await stats_service.get_match_with_cached_stats(match_id)
        return {
            "match_id": match_id,
            "statistics": stats,
            "server_time_ms": int(time.time() * 1000),
        }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching stats: {e}", exc_info=True)
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


async def fetch_matches_with_data_by_tournament_paginated(
    tournament_id: int,
    skip: int = 0,
    limit: int = 7,
    order_exp: str = "id",
    order_exp_two: str = "id",
    database=None,
) -> Any:
    fetch_data_logger.debug("Fetching list of matches with full data")

    _db = database or db
    tournament_service_db = TournamentServiceDB(_db)

    try:
        # Fetch matches with pagination
        paginated_matches = await tournament_service_db.get_matches_by_tournament_with_pagination(
            tournament_id, skip, limit, order_exp, order_exp_two
        )

        match_ids = [match.id for match in paginated_matches]
        fetch_data_logger.debug(f"Fetched match_ids {match_ids}")

        fetch_data_logger.debug(f"Fetched {len(match_ids)} of matches")

        if len(match_ids) == 0:
            fetch_data_logger.info(
                f"No matches in tournament id:{tournament_id} on page:{skip} with limit:{limit}"
            )
            return []

        # Fetch full match details for all matches in parallel
        full_match_data_list = await asyncio.gather(
            *[fetch_with_scoreboard_data(match_id, database=_db) for match_id in match_ids]
        )

        fetch_data_logger.debug(
            f"Fetched {len(match_ids)} matches with full data for tournament_id: {tournament_id}"
        )

        return full_match_data_list

    except Exception as e:
        fetch_data_logger.error(f"Error fetching tournament matches data: {e}", exc_info=True)
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": str(e),
        }


def instance_to_dict(instance: dict[str, Any]) -> dict[str, Any] | None:
    try:
        result_dict = {key: value for key, value in instance.items() if not key.startswith("_")}
        return result_dict
    except Exception as e:
        logger.error(f"Error converting instance to dictionary: {e}")
        return None


def deep_dict_convert(obj: dict[str, Any]) -> dict[str, Any] | None:
    try:
        result_dict = {}
        for key, value in obj.items():
            if not key.startswith("_"):
                if isinstance(value, datetime.datetime):  # check against datetime.datetime
                    result_dict[key] = value.isoformat()
                elif isinstance(value, dict):
                    result_dict[key] = deep_dict_convert(value)
                elif isinstance(value, list):
                    result_dict[key] = [
                        deep_dict_convert(item.__dict__)
                        if hasattr(item, "__dict__")
                        else deep_dict_convert(item)
                        if isinstance(item, dict)
                        else item
                        for item in value
                    ]
                elif hasattr(value, "__dict__"):
                    result_dict[key] = deep_dict_convert(value.__dict__)
                else:
                    result_dict[key] = value
        return result_dict
    except Exception as e:
        logger.error(f"Error in deep dictionary convert: {e}")
        return None


async def _fetch_events_by_match(match_id: int, database=None) -> list:
    from src.core.models.football_event import FootballEventDB

    _db = database or db
    fetch_data_logger.debug(f"Fetching events for match_id:{match_id}")
    async with _db.get_session_maker()() as session:
        stmt = select(FootballEventDB).where(FootballEventDB.match_id == match_id)
        result = await session.execute(stmt)
        events = result.scalars().all()
        fetch_data_logger.debug(f"Fetched {len(events)} events for match_id:{match_id}")
        return events
