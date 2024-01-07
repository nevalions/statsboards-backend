from typing import List
from fastapi import HTTPException, Request, Depends, status

from src.core import db
from src.matchdata.db_services import MatchDataServiceDB
from src.matchdata.schemas import MatchDataSchemaCreate
from src.matches.db_services import MatchServiceDB


async def fetch_match_data(matches: List):
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
                "status_code": status.HTTP_200_OK,
                "match": match,
                "teams_data": match_teams_data,
                "match_data": match_data.__dict__,
            }
        )

    return all_match_data
