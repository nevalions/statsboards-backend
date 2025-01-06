import datetime
import logging
from typing import List

from fastapi import status

from src.core import db
from src.gameclocks.db_services import GameClockServiceDB
from src.gameclocks.schemas import GameClockSchemaCreate
from src.logging_config import setup_logging
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.playclocks.db_services import PlayClockServiceDB
from src.playclocks.schemas import PlayClockSchemaCreate
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.shemas import ScoreboardSchemaCreate

setup_logging()
logger = logging.getLogger("backend_logger_helpers")
fetch_data_logger = logging.getLogger("backend_fetch_data_helpers")


async def fetch_list_of_matches_data(matches: List):
    fetch_data_logger.debug("Fetching list of matches data")
    from src.matches.db_services import MatchServiceDB

    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)
    all_match_data = []

    try:
        for match in matches:
            match_id = match.id
            match_teams_data = await match_service_db.get_teams_by_match(match_id)
            match_data = await match_service_db.get_matchdata_by_match(match_id)

            if match_data is None:
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                match_data = await match_data_service_db.create_match_data(
                    match_data_schema
                )

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
        fetch_data_logger.error(
            f"Error while fetching list of matches data: {e}", exc_info=True
        )


async def fetch_match_data(match_id: int):
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Fetching matchdata by mathc_id:{match_id}")
    try:
        match_data_service_db = MatchDataServiceDB(db)
        match_service_db = MatchServiceDB(db)

        match = await match_service_db.get_by_id(match_id)
        match_teams_data = await match_service_db.get_teams_by_match(match_id)
        match_data = await match_service_db.get_matchdata_by_match(match_id)

        if match:
            if match_data is None:
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                match_data = await match_data_service_db.create_match_data(
                    match_data_schema
                )

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


async def fetch_with_scoreboard_data(match_id: int):
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching match data with match_id {match_id}")
    scoreboard_data_service = ScoreboardServiceDB(db)
    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)

    try:
        scoreboard_data = await match_service_db.get_scoreboard_by_match(match_id)
        fetch_data_logger.debug(f"Scoreboard Data: {scoreboard_data}")

        match = await match_service_db.get_by_id(match_id)
        fetch_data_logger.debug(f"Match by match_id:{match_id} {match}")

        match_teams_data = await match_service_db.get_teams_by_match(match_id)
        fetch_data_logger.debug(
            f"Match teams by match_id:{match_id} {match_teams_data}"
        )

        match_data = await match_service_db.get_matchdata_by_match(match_id)
        fetch_data_logger.debug(f"Match Data by match_id:{match_id} {match_data}")

        if match:
            if match_data is None:
                fetch_data_logger.debug(
                    f"Match Data not found for match_id:{match_id}, creating new..."
                )
                match_data_schema = MatchDataSchemaCreate(match_id=match_id)
                fetch_data_logger.debug(f"Schema for match data {match_data_schema}")
                match_data = await match_data_service_db.create_match_data(
                    match_data_schema
                )
            if scoreboard_data is None:
                fetch_data_logger.debug(
                    f"Scoreboard Data not found for match_id:{match_id}, creating new..."
                )
                scoreboard_data_schema = ScoreboardSchemaCreate(match_id=match_id)
                fetch_data_logger.debug(
                    f"Schema for scoreboard data {scoreboard_data_schema}"
                )
                scoreboard_data = await scoreboard_data_service.create_scoreboard(
                    scoreboard_data_schema
                )

            final_match_with_scoreboard_data_fetched = {
                "data": {
                    "match_id": match_id,
                    "id": match_id,
                    "status_code": status.HTTP_200_OK,
                    "match": deep_dict_convert(match.__dict__),
                    "scoreboard_data": instance_to_dict(scoreboard_data.__dict__),
                    "teams_data": deep_dict_convert(match_teams_data),
                    "match_data": instance_to_dict(match_data.__dict__),
                }
            }
            fetch_data_logger.debug(
                f"Final match with scoreboard data fetched {final_match_with_scoreboard_data_fetched}"
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


async def fetch_gameclock(match_id: int):
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching gemeclock with match_id:{match_id}")
    gameclock_service = GameClockServiceDB(db)
    match_service_db = MatchServiceDB(db)

    try:
        match = await match_service_db.get_by_id(match_id)
        gameclock = await gameclock_service.get_gameclock_by_match_id(match_id)

        if match:
            if gameclock is None:
                gameclock_schema = GameClockSchemaCreate(match_id=match_id)
                gameclock = await gameclock_service.create_gameclock(gameclock_schema)
            return {
                "match_id": match_id,
                "id": match_id,
                "status_code": status.HTTP_200_OK,
                "gameclock": instance_to_dict(gameclock.__dict__),
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching gameclock: {e}", exc_info=True)


async def fetch_playclock(match_id: int):
    from src.matches.db_services import MatchServiceDB

    fetch_data_logger.debug(f"Starting fetching playclock with match_id:{match_id}")
    playclock_service = PlayClockServiceDB(db)
    match_service_db = MatchServiceDB(db)
    try:
        match = await match_service_db.get_by_id(match_id)
        playclock = await playclock_service.get_playclock_by_match_id(match_id)

        if match:
            if playclock is None:
                playclock_schema = PlayClockSchemaCreate(match_id=match_id)
                playclock = await playclock_service.create_playclock(playclock_schema)
            return {
                "match_id": match_id,
                "id": match_id,
                "status_code": status.HTTP_200_OK,
                "playclock": instance_to_dict(playclock.__dict__),
            }
        else:
            return {
                "status_code": status.HTTP_404_NOT_FOUND,
            }
    except Exception as e:
        fetch_data_logger.error(f"Error while fetching playclock: {e}", exc_info=True)


def instance_to_dict(instance):
    logger.debug(f"Instance to dictionary convert instance: {instance}")
    logger.debug(f"Instance to dictionary convert instance type: {type(instance)}")
    try:
        result_dict = {
            key: value for key, value in instance.items() if not key.startswith("_")
        }
        logger.info(
            f"Instance to dictionary completed successfully. Result: {result_dict}"
        )
        return result_dict
    except Exception as e:
        logger.error(f"Error converting instance to dictionary: {e}")
        return None


def deep_dict_convert(obj):
    logger.debug(f"Deep dictionary convert object: {obj}")
    logger.debug(f"Deep dictionary convert object type: {type(obj)}")
    try:
        result_dict = {}
        for key, value in obj.items():
            if not key.startswith("_"):
                if isinstance(
                    value, datetime.datetime
                ):  # check against datetime.datetime
                    logger.info(f"Converting {key} to datetime")
                    result_dict[key] = value.isoformat()
                elif isinstance(value, dict):
                    logger.info(f"Converting {key} to dict")
                    result_dict[key] = deep_dict_convert(value)
                else:
                    result_dict[key] = value
        logger.debug(
            f"Deep dictionary convert completed successfully. Result: {result_dict}"
        )
        return result_dict
    except Exception as e:
        logger.error(f"Error in deep dictionary convert: {e}")
        return None
