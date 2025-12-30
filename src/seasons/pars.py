from fastapi import APIRouter, HTTPException

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
