import datetime
from typing import List
from fastapi import HTTPException, Request, Depends, status

from src.core import db
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.matches.db_services import MatchServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from src.scoreboards.shemas import ScoreboardSchemaCreate


async def fetch_list_of_matches_data(matches: List):
    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)
    all_match_data = []

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


async def fetch_match_data(match_id: int):
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


async def fetch_with_scoreboard_data(match_id: int):
    scoreboard_data_service = ScoreboardServiceDB(db)
    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)

    # print("Before getting scoreboard_data")
    scoreboard_data = await match_service_db.get_scoreboard_by_match(match_id)
    # print("Scoreboard Data:", scoreboard_data)

    # print("Before getting match")
    match = await match_service_db.get_by_id(match_id)
    # print("Scoreboard Data:", match)

    # print("Before getting match_teams_data")
    match_teams_data = await match_service_db.get_teams_by_match(match_id)
    #     print("Scoreboard Data:", match_teams_data)

    #     print("Before getting match_data")
    match_data = await match_service_db.get_matchdata_by_match(match_id)
    #     print("Scoreboard Data:", match_data)

    if match:
        if match_data is None:
            match_data_schema = MatchDataSchemaCreate(match_id=match_id)
            match_data = await match_data_service_db.create_match_data(
                match_data_schema
            )
        if scoreboard_data is None:
            scoreboard_data_schema = ScoreboardSchemaCreate(match_id=match_id)
            scoreboard_data = await scoreboard_data_service.create_scoreboard(
                scoreboard_data_schema
            )

        return {
            "match_id": match_id,
            "id": match_id,
            "status_code": status.HTTP_200_OK,
            "match": deep_dict(match.__dict__),
            "scoreboard_data": instance_to_dict(scoreboard_data.__dict__),
            "teams_data": deep_dict(match_teams_data),
            "match_data": instance_to_dict(match_data.__dict__),
        }
    else:
        return {
            "status_code": status.HTTP_404_NOT_FOUND,
        }


def instance_to_dict(instance):
    result_dict = {key: value for key, value in instance.items() if not key.startswith('_')}
    return result_dict


def deep_dict(obj):
    result_dict = {}
    for key, value in obj.items():
        if not key.startswith('_'):
            if isinstance(value, datetime.datetime):  # check against datetime.datetime
                result_dict[key] = value.isoformat()
            elif isinstance(value, dict):
                result_dict[key] = deep_dict(value)
            else:
                result_dict[key] = value
    return result_dict
