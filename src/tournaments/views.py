import json
from typing import List, Optional

from fastapi import Depends, File, HTTPException, Path, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from src.core import BaseRouter, MinimalBaseRouter, db
from src.core.config import templates
from src.helpers.fetch_helpers import fetch_list_of_matches_data
from src.pars_eesl.pars_season import parse_season_and_create_jsons
from src.seasons.db_services import SeasonServiceDB

from ..helpers.file_service import file_service
from ..logging_config import get_logger, setup_logging
from ..sponsor_lines.schemas import SponsorLineSchema
from ..sponsors.schemas import SponsorSchema
from .db_services import TournamentServiceDB
from .schemas import (
    TournamentSchema,
    TournamentSchemaCreate,
    TournamentSchemaUpdate,
    UploadResizeTournamentLogoResponse,
    UploadTournamentLogoResponse,
)

setup_logging()


class TournamentAPIRouter(
    BaseRouter[TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate]
):
    def __init__(self, service: TournamentServiceDB):
        super().__init__(
            "/api/tournaments",
            ["tournaments-api"],
            service,
        )
        self.logger = get_logger("backend_logger_TournamentAPIRouter", self)
        self.logger.debug("Initialized TournamentAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=TournamentSchema,
        )
        async def create_tournament_endpoint(item: TournamentSchemaCreate):
            self.logger.debug(f"Create or update tournament endpoint got data: {item}")
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
            self.logger.debug(f"Update tournament endpoint id:{item_id} data: {item}")
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
            self.logger.debug(
                f"Get tournament by eesl_id endpoint got eesl_id:{eesl_id}"
            )
            tournament = await self.service.get_tournament_by_eesl_id(value=eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({eesl_id}) not found",
                )
            return tournament.__dict__

        @router.get("/id/{tournament_id}/teams/")
        async def get_teams_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(f"Get teams by tournament id:{tournament_id} endpoint")
            return await self.service.get_teams_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/players/")
        async def get_players_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(f"Get players by tournament id:{tournament_id} endpoint")
            return await self.service.get_players_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/matches/count")
        async def get_count_of_matches_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(
                f"Get count of matches by tournament id:{tournament_id} endpoint"
            )
            return await self.service.get_count_of_matches_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/matches/")
        async def get_matches_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(f"Get matches by tournament id:{tournament_id} endpoint")
            return await self.service.get_matches_by_tournament(tournament_id)

        @router.get(
            "/id/{tournament_id}/matches/page/{page}/items_per_page/{items_per_page}/order_one/{order_exp}/order_two/{order_exp_two}"
        )
        async def get_tournament_matches_with_pagination_endpoint(
            tournament_id: int,
            page: int = Path(..., ge=1),
            items_per_page: int = Path(..., ge=1, le=100),
            order_exp: str = "id",
            order_exp_two: str = "id",
        ):
            self.logger.debug(
                f"Get matches by tournament id:{tournament_id} with pagination and order endpoint"
            )
            skip = (page - 1) * items_per_page
            matches = await self.service.get_matches_by_tournament_with_pagination(
                tournament_id=tournament_id,
                skip=skip,
                limit=items_per_page,
                order_exp=order_exp,
                order_exp_two=order_exp_two,
            )
            return matches

        @router.get(
            "/id/{tournament_id}/main_sponsor/", response_model=Optional[SponsorSchema]
        )
        async def get_main_sponsor_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(
                f"Get main_tournament_sponsor by tournament id:{tournament_id} endpoint"
            )
            return await self.service.get_main_tournament_sponsor(tournament_id)

        @router.get(
            "/id/{tournament_id}/sponsor_line/",
            response_model=Optional[SponsorLineSchema],
        )
        async def get_sponsor_line_by_tournament_id_endpoint(tournament_id: int):
            self.logger.debug(
                f"Get tournament_sponsor_line by tournament id:{tournament_id} endpoint"
            )
            return await self.service.get_tournament_sponsor_line(tournament_id)

        @router.get(
            "/id/{tournament_id}/sponsors/",
            response_model=Optional[List[SponsorSchema]],
        )
        async def get_sponsors_from_sponsor_line_by_tournament_id_endpoint(
            tournament_id: int,
        ):
            self.logger.debug(
                f"Get sponsors_from_sponsor_line by tournament id:{tournament_id} endpoint"
            )
            return await self.service.get_sponsors_of_tournament_sponsor_line(
                tournament_id
            )

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
            file_location = await file_service.save_upload_image(
                file, sub_folder="tournaments/logos"
            )
            self.logger.debug(
                f"Upload and resize tournament logo endpoint file location: {file_location}"
            )
            return {"logoUrl": file_location}

        @router.post(
            "/upload_resize_logo", response_model=UploadResizeTournamentLogoResponse
        )
        async def upload_and_resize_tournament_logo_endpoint(
            file: UploadFile = File(...),
        ):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder="tournaments/logos",
                icon_height=100,
                web_view_height=400,
            )
            self.logger.debug(
                f"Upload and resize tournament logo endpoint file location: {uploaded_paths}"
            )
            return uploaded_paths

        @router.get(
            "/pars/season/{eesl_season_id}",
            response_model=List[TournamentSchemaCreate],
        )
        async def get_parsed_season_tournaments_endpoint(eesl_season_id: int):
            self.logger.debug(
                f"Get parsed tournaments from season eesl_id:{eesl_season_id} endpoint"
            )
            return await parse_season_and_create_jsons(eesl_season_id)

        @router.post("/pars_and_create/season/{eesl_season_id}")
        async def create_parsed_tournament_endpoint(
            eesl_season_id: int,
        ):
            self.logger.debug(
                f"Get and Save parsed tournaments from season eesl_id:{eesl_season_id} endpoint"
            )
            tournaments_list = await parse_season_and_create_jsons(eesl_season_id)

            created_tournaments = []
            try:
                if tournaments_list:
                    for t in tournaments_list:
                        tournament = TournamentSchemaCreate(**t)
                        created_tournament = (
                            await self.service.create_or_update_tournament(tournament)
                        )
                        self.logger.debug(
                            f"Created or updated tournament after parse {created_tournament}"
                        )
                        created_tournaments.append(created_tournament)
                    self.logger.info(
                        f"Created tournaments after parsing: {created_tournaments}"
                    )
                    return created_tournaments
                else:
                    self.logger.warning("Teams list is empty")
                    return []
            except Exception as ex:
                self.logger.error(
                    f"Error on parse and tournaments from season: {ex}",
                    exc_info=True,
                )

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
