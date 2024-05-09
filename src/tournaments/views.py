import json
from typing import List, Optional

from fastapi import HTTPException, Request, Depends, UploadFile, File

from fastapi.responses import JSONResponse, HTMLResponse

from src.core import BaseRouter, MinimalBaseRouter, db
from src.core.config import templates, uploads_path
from .db_services import TournamentServiceDB
from .schemas import TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate, UploadTournamentLogoResponse, \
    UploadResizeTournamentLogoResponse
from src.helpers.fetch_helpers import fetch_list_of_matches_data
from src.seasons.db_services import SeasonServiceDB
from src.pars_eesl.pars_season import parse_season_and_create_jsons
from ..helpers.file_service import file_service
from ..sponsor_lines.schemas import SponsorLineSchema
from ..sponsors.schemas import SponsorSchema


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
            "/{item_id}/",
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

        @router.get("/id/{tournament_id}/teams/")
        async def get_teams_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_teams_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/players/")
        async def get_players_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_players_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/matches/")
        async def get_matches_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_matches_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/main_sponsor/",
                    response_model=Optional[SponsorSchema])
        async def get_main_sponsor_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_main_tournament_sponsor(tournament_id)

        @router.get("/id/{tournament_id}/sponsor_line/",
                    response_model=Optional[SponsorLineSchema])
        async def get_sponsor_line_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_tournament_sponsor_line(tournament_id)

        @router.get("/id/{tournament_id}/sponsors/",
                    response_model=Optional[List[SponsorSchema]]
                    )
        async def get_sponsors_from_sponsor_line_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_sponsors_of_tournament_sponsor_line(tournament_id)

        @router.get(
            "/id/{tournament_id}/matches/all/data/",
            response_class=JSONResponse,
        )
        async def all_tournament_matches_data_endpoint(
                tournament_id: int,
                all_matches: List = Depends(self.service.get_matches_by_tournament),
        ):
            if not all_matches:
                return []
            return await fetch_list_of_matches_data(all_matches)

        @router.post("/upload_logo", response_model=UploadTournamentLogoResponse)
        async def upload_tournament_logo_endpoint(file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder='tournaments/logos')
            print(uploads_path)
            return {"logoUrl": file_location}

        @router.post("/upload_resize_logo", response_model=UploadResizeTournamentLogoResponse)
        async def upload_and_resize_tournament_logo_endpoint(file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder='tournaments/logos',
                icon_height=100,
                web_view_height=400,
            )
            print(uploads_path)
            return uploaded_paths

        @router.get(
            "/pars/season/{eesl_season_id}",
            response_model=List[TournamentSchemaCreate],
        )
        async def get_parsed_season_tournaments_endpoint(eesl_season_id: int):
            return await parse_season_and_create_jsons(eesl_season_id)

        @router.post("/pars_and_create/season/{eesl_season_id}")
        async def create_parsed_tournament_endpoint(
                eesl_season_id: int,
        ):
            tournaments_list = await parse_season_and_create_jsons(eesl_season_id)

            created_tournaments = []
            if tournaments_list:
                for t in tournaments_list:
                    tournament = TournamentSchemaCreate(**t)
                    created_tournament = await self.service.create_or_update_tournament(tournament)
                    created_tournaments.append(created_tournament)
                return created_tournaments
            else:
                return []

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

        @router.get(
            "/id/{tournament_id}/matches/create/",
            response_class=HTMLResponse,
        )
        async def create_match_in_tournament_endpoint(
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
            response_class=HTMLResponse,
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
