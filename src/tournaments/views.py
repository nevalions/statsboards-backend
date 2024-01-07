import json
from typing import List

from fastapi import HTTPException, Request, Depends, status

from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from src.core.config import templates
from .db_services import TournamentServiceDB
from .schemas import TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate
from src.helpers.fetch_helpers import fetch_match_data
from src.seasons.db_services import SeasonServiceDB
from ..core.base_router import MinimalBaseRouter


class TournamentAPIRouter(
    BaseRouter[TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate]
):
    def __init__(self, service: TournamentServiceDB):
        super().__init__(
            "/api/tournaments",
            ["tournaments-api"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=TournamentSchema,
        )
        async def create_tournament_endpoint(item: TournamentSchemaCreate):
            new_ = await self.service.create_or_update_tournament(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=TournamentSchema,
        )
        async def update_tournament_endpoint(
            item_id: int,
            item: TournamentSchemaUpdate,
        ):
            update_ = await self.service.update_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=TournamentSchema,
        )
        async def get_tournament_by_eesl_id_endpoint(eesl_id: int):
            tournament = await self.service.get_tournament_by_eesl_id(value=eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.get(
            "/id/{tournament_id}/teams/",
            # response_model=List[TeamSchema]
        )
        async def get_teams_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_teams_by_tournament(tournament_id)

        @router.get(
            "/id/{tournament_id}/matches/",
            # response_model=List[TeamSchema]
        )
        async def get_matches_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_matches_by_tournament(tournament_id)

        @router.get(
            "/id/{tournament_id}/matches/all/data/", response_class=JSONResponse
        )
        async def all_tournament_matches_data_endpoint(
            tournament_id: int,
            all_matches: List = Depends(self.service.get_matches_by_tournament),
        ):
            if not all_matches:
                raise HTTPException(
                    status_code=404, detail="No matches found for the tournament"
                )
            return await fetch_match_data(all_matches)

        return router


class TournamentTemplateRouter(
    MinimalBaseRouter[TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate]
):
    def __init__(self, service: TournamentServiceDB):
        super().__init__(
            "/tournaments",
            ["tournaments-templ"],
            service,
        )

    def route(self):
        router = super().route()

        @router.get("/id/{tournament_id}/matches/create/")
        async def create_match_in_tournament(
            tournament_id: int,
            request: Request,
        ):
            tournament = await self.service.get_by_id(tournament_id)
            season_service_db = SeasonServiceDB(db)
            season = await season_service_db.get_by_id(tournament.season_id)
            tournament_dict = self.service.to_dict(tournament)
            season_dict = season_service_db.to_dict(season)

            return templates.TemplateResponse(
                "/matches/display/create-match.html",
                {
                    "request": request,
                    "tournament": json.dumps(tournament_dict),
                    "season": json.dumps(season_dict),
                    "tournament_id": tournament_id,
                    "season_id": season.id,
                    "tournament_title": tournament.title,
                },
                status_code=200,
            )

        @router.get(
            "/id/{tournament_id}/matches/all/",
            response_class=JSONResponse,
        )
        async def get_all_tournament_matches_endpoint(
            tournament_id: int,
            request: Request,
        ):
            tournament = await self.service.get_by_id(tournament_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament id: {tournament_id} not found",
                )
            template = templates.TemplateResponse(
                name="/matches/display/all-tournament-matches.html",
                context={
                    "request": request,
                    "tournament_id": tournament_id,
                    "tournament_title": tournament.title,
                },
                status_code=200,
            )
            return template

        return router


api_tournament_router = TournamentAPIRouter(TournamentServiceDB(db)).route()
template_tournament_router = TournamentTemplateRouter(TournamentServiceDB(db)).route()
