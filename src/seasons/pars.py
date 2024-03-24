from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.core.models.base import get_db_session
from src.pars_eesl import BASE_SEASON_URL
from src.pars_eesl.pars_season import parse_season_and_create_jsons
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate

api_pars_season_router = APIRouter()


@api_pars_season_router.get("/api/pars/season/{eesl_season_id}", tags=["pars"])
async def get_parsed_season(eesl_season_id: int):
    full_season_data = parse_season_and_create_jsons(eesl_season_id)
    if full_season_data:
        return full_season_data
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Season {BASE_SEASON_URL}{eesl_season_id} not found",
        )

# @api_pars_season_router.post("/api/pars/season/{eesl_season_id}",
#                              tags=["pars"])
# async def create_parsed_tournament(
#         eesl_season_id: int,
#         db: Session = Depends(get_db_session),
#
# ):
#     tournament_service = TournamentServiceDB(db)
#     full_season_data = parse_season_and_create_jsons(eesl_season_id)
#     created_data = []
#     print(created_data)
#     if full_season_data:
#         for t in full_season_data:
#             print(t)
#             tournament = TournamentSchemaCreate(**t)
#             created_tournament = await tournament_service.create_or_update_tournament(tournament)
#             created_data.append(created_tournament.__dict__)
#     else:
#         raise HTTPException(status_code=404,
#                             detail=f"Season {BASE_SEASON_URL}{eesl_season_id} "
#                                    f"not found")
#     return created_data
