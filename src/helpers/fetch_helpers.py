from typing import List
from fastapi import HTTPException, Request, Depends, status

from src.core import db
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.matches.db_services import MatchServiceDB


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
    match_data_service_db = MatchDataServiceDB(db)
    match_service_db = MatchServiceDB(db)

    scoreboard_data = await match_service_db.get_scoreboard_by_match(match_id)
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
            "scoreboard_data": scoreboard_data,
            "teams_data": match_teams_data,
            "match_data": match_data.__dict__,
        }
    else:
        return {
            "status_code": status.HTTP_404_NOT_FOUND,
        }
