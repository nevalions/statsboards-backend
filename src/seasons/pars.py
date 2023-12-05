from pprint import pprint

from fastapi import APIRouter, HTTPException, Depends

# from src.async_db.tournaments import TournamentServiceDB, get_tournament_db
# from src.schemas import TournamentSchemaCreate

from src.pars_eesl import BASE_SEASON_URL
from src.pars_eesl.pars_season import parse_season_and_create_jsons

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


#
# @api_pars_season_router.post("/api/pars/season/{eesl_season_id}",
#                              tags=["pars"])
# async def create_parsed_tournament(
#         eesl_season_id: int,
#         tournament_service: TournamentServiceDB = Depends(get_tournament_db)
# ):
#     full_season_data = parse_season_and_create_jsons(eesl_season_id)
#     created_data = []
#     if full_season_data:
#         for t in full_season_data:
#             tournament = TournamentSchemaCreate(**t)
#             created_tournament = await tournament_service.create_tournament(tournament)
#             created_data.append(created_tournament.__dict__)
#     else:
#         raise HTTPException(status_code=404,
#                             detail=f"Season {BASE_SEASON_URL}{eesl_season_id} "
#                                    f"not found")
#     return created_data
