import asyncio
import logging
from typing import List

from fastapi import HTTPException, Request, Depends, status, WebSocket, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.websockets import WebSocketDisconnect, WebSocketState
from websockets import ConnectionClosedOK

from src.core import BaseRouter, db, MinimalBaseRouter
from .db_services import MatchServiceDB
from .shemas import (
    MatchSchemaCreate,
    MatchSchemaUpdate,
    MatchSchema,

)
from src.core.config import templates

from src.matchdata.db_services import MatchDataServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from ..core.models.base import ws_manager, connection_manager
from ..gameclocks.db_services import GameClockServiceDB
from ..gameclocks.schemas import GameClockSchemaCreate
from ..helpers.file_service import file_service
from ..matchdata.schemas import MatchDataSchemaCreate
from ..pars_eesl.pars_tournament import parse_tournament_matches_index_page_eesl
from ..playclocks.db_services import PlayClockServiceDB
from ..playclocks.schemas import PlayClockSchemaCreate
from ..scoreboards.shemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from ..sponsors.db_services import SponsorServiceDB
from ..teams.db_services import TeamServiceDB
from ..teams.schemas import UploadTeamLogoResponse, UploadResizeTeamLogoResponse
from ..tournaments.db_services import TournamentServiceDB


# Match backend
class MatchAPIRouter(
    BaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches-api"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=MatchSchema,
        )
        async def create_match_endpoint(
                match: MatchSchemaCreate,
        ):
            new_match = await self.service.create_or_update_match(match)
            return new_match.__dict__

        @router.post(
            "/create_with_full_data/",
        )
        async def create_match_with_full_data_endpoint(
                data: MatchSchemaCreate,
        ):
            # print(data)
            teams_service = TeamServiceDB(db)
            tournament_service = TournamentServiceDB(db)
            sponsor_service = SponsorServiceDB(db)
            match_db_service = MatchDataServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_db_service = ScoreboardServiceDB(db)

            # Create all
            new_match = await self.service.create_or_update_match(data)

            default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
            default_playclock = PlayClockSchemaCreate(match_id=new_match.id)
            default_gameclock = GameClockSchemaCreate(match_id=new_match.id)

            tournament = await tournament_service.get_by_id(new_match.tournament_id)
            tournament_main_sponsor = await sponsor_service.get_by_id(tournament.main_sponsor_id)
            team_a = await teams_service.get_by_id(new_match.team_a_id)
            team_b = await teams_service.get_by_id(new_match.team_b_id)

            existing_scoreboard = await scoreboard_db_service.get_scoreboard_by_match_id(new_match.id)

            if existing_scoreboard is None:
                scoreboard_schema = ScoreboardSchemaCreate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=tournament_main_sponsor.scale_logo,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title,
                    team_b_game_title=team_b.title,
                )
            else:
                scoreboard_schema = ScoreboardSchemaUpdate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=tournament_main_sponsor.scale_logo,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title,
                    team_b_game_title=team_b.title,
                )
            new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(scoreboard_schema)

            new_match_data = await match_db_service.create_match_data(default_match_data)
            teams_data = await self.service.get_teams_by_match(new_match_data.match_id)
            # new_scoreboard = await scoreboard_db_service.create_scoreboard(
            #     default_scoreboard
            # )

            # Return the created objects
            return {
                "status_code": status.HTTP_200_OK,
                "match": new_match,
                "match_data": new_match_data,
                "teams_data": teams_data,
                "scoreboard": new_scoreboard,
            }

        @router.put(
            "/{item_id}/",
            response_model=MatchSchema,
        )
        async def update_match_endpoint(
                item_id: int,
                item: MatchSchemaUpdate,
        ):
            match_update = await self.service.update_match(item_id, item)

            if match_update is None:
                raise HTTPException(
                    status_code=404, detail=f"Match id({item_id}) " f"not found"
                )
            return match_update.__dict__

        @router.get(
            "/eesl_id/{eesl_id}/",
            response_model=MatchSchema,
        )
        async def get_match_by_eesl_id_endpoint(eesl_id: int):
            match = await self.service.get_match_by_eesl_id(value=eesl_id)
            if match is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match eesl_id({eesl_id}) " f"not found",
                )
            return match.__dict__

        @router.get(
            "/id/{match_id}/teams/",
        )
        async def get_match_teams_by_match_id_endpoint(match_id: int):
            return await self.service.get_teams_by_match(match_id)

        @router.get(
            "/id/{match_id}/match_data/",
        )
        async def get_match_data_by_match_id_endpoint(match_id: int):
            return await self.service.get_matchdata_by_match(match_id)

        @router.get(
            "/id/{match_id}/playclock/",
        )
        async def get_playclock_by_match_id_endpoint(match_id: int):
            return await self.service.get_playclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/gameclock/",
        )
        async def get_gameclock_by_match_id_endpoint(match_id: int):
            return await self.service.get_gameclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard_data/",
        )
        async def get_match_scoreboard_by_match_id_endpoint(match_id: int):
            return await self.service.get_scoreboard_by_match(match_id)

        @router.get("/all/data/", response_class=JSONResponse)
        async def all_matches_data_endpoint_endpoint(
                all_matches: List = Depends(self.service.get_all_elements),
        ):
            from src.helpers.fetch_helpers import fetch_list_of_matches_data

            return await fetch_list_of_matches_data(all_matches)

        @router.get(
            "/id/{match_id}/data/",
            response_class=JSONResponse,
        )
        async def match_data_endpoint(
                # request: Request,
                # match_id: int,
                match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
                match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            return (
                {
                    "status_code": status.HTTP_200_OK,
                    "teams_data": match_teams_data,
                    "match_data": match_data.__dict__,
                },
            )

        @router.get(
            "/id/{match_id}/scoreboard/full_data/",
            response_class=JSONResponse,
        )
        async def full_match_data_endpoint(match_id: int):
            from src.helpers.fetch_helpers import fetch_match_data

            return await fetch_match_data(match_id)

        @router.get(
            "/id/{match_id}/scoreboard/full_data/scoreboard_settings/",
            response_class=JSONResponse,
        )
        async def full_match_data_with_scoreboard_endpoint(match_id: int):
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            return await fetch_with_scoreboard_data(match_id)

        @router.post("/id/{match_id}/upload_team_logo", response_model=UploadTeamLogoResponse)
        async def upload_team_logo(match_id: int, file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder=f'match/{match_id}/teams_logos')
            return {"logoUrl": file_location}

        @router.post("/id/{match_id}/upload_resize_logo", response_model=UploadResizeTeamLogoResponse)
        async def upload_resize_team_logo(match_id: int, file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder=f'match/{match_id}/teams_logos',
                icon_height=100,
                web_view_height=400,
            )
            # print(uploaded_paths)
            return uploaded_paths

        @router.websocket("/ws/id/{match_id}/{client_id}/")
        async def websocket_endpoint(websocket: WebSocket, client_id: str, match_id: int):
            await connection_manager.connect(websocket, client_id, match_id)
            await ws_manager.connect(client_id)
            logger = logging.getLogger('websocket_endpoint')
            await websocket.accept()

            try:
                from src.helpers.fetch_helpers import fetch_with_scoreboard_data, fetch_playclock, fetch_gameclock

                initial_data = await fetch_with_scoreboard_data(match_id)
                initial_data['type'] = 'message-update'
                print(['WebSocket Connection', initial_data])
                await websocket.send_json(initial_data)

                initial_playclock_data = await fetch_playclock(match_id)
                initial_playclock_data['type'] = 'playclock-update'
                await websocket.send_json(initial_playclock_data)
                print(['WebSocket Connection', initial_playclock_data])

                initial_gameclock_data = await fetch_gameclock(match_id)
                initial_gameclock_data['type'] = 'gameclock-update'
                await websocket.send_json(initial_gameclock_data)
                print(['WebSocket Connection', initial_gameclock_data])

                await process_data_websocket(websocket, client_id, match_id)

                # await asyncio.gather(
                #     process_match_data_websocket(websocket, client_id, match_id),
                #     process_gameclock_data(websocket, client_id, match_id),
                #     process_playclock_data(websocket, client_id, match_id),
                #     return_exceptions=True
                # )
            except WebSocketDisconnect:
                logger.error('WebSocket disconnect:', exc_info=True)
            except ConnectionClosedOK:
                logger.error('ConnectionClosedOK:', exc_info=True)
            except asyncio.TimeoutError:
                logger.error('TimeoutError:', exc_info=True)
            except RuntimeError:
                logger.error('RuntimeError:', exc_info=True)
            except Exception as e:
                logger.error(f'Unexpected error:{str(e)}', exc_info=True)
            finally:
                await connection_manager.disconnect(client_id)
                await ws_manager.disconnect(client_id)

        async def process_data_websocket(websocket: WebSocket, client_id: str, match_id: int):
            handlers = {
                'matchdata': process_match_data,
                'gameclock': process_gameclock_data,
                'playclock': process_playclock_data,
                'match': process_match_data,
                'scoreboard': process_match_data,
            }

            while websocket.application_state == WebSocketState.CONNECTED:
                data = await connection_manager.queues[client_id].get()
                print(f'[DEBUG] client {client_id}: {data}')

                handler = handlers.get(data.get('table'))

                if not handler:
                    print(f'[WARNING] No handler for table {data.get("table")}')
                    continue

                try:
                    await handler(websocket, match_id)
                except Exception as e:
                    print(f'[ERROR] client {client_id}, table {data.get("table")}: {e}')

        async def process_match_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data
            full_match_data = await fetch_with_scoreboard_data(match_id)
            full_match_data['type'] = 'match-update'
            print('[WebSocket Connection] Full match data fetched: ', full_match_data)
            await websocket.send_json(full_match_data)

        async def process_gameclock_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_gameclock
            gameclock_data = await fetch_gameclock(match_id)
            gameclock_data['type'] = 'gameclock-update'
            print('[WebSocket Connection] Gameclock data fetched: ', gameclock_data)
            await websocket.send_json(gameclock_data)

        async def process_playclock_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_playclock
            playclock_data = await fetch_playclock(match_id)
            playclock_data['type'] = 'playclock-update'
            print('[WebSocket Connection] Playclock data fetched: ', playclock_data)
            await websocket.send_json(playclock_data)

        @router.get(
            "/api/pars/tournament/{eesl_tournament_id}",
            # response_model=List[MatchSchemaCreate],
        )
        async def get_parse_tournament_matches(eesl_tournament_id: int):
            return await parse_tournament_matches_index_page_eesl(eesl_tournament_id)

        @router.post(
            "/add"
        )
        async def create_match_with_full_data_and_scoreboard_endpoint(
                data: MatchSchemaCreate,
        ):
            teams_service = TeamServiceDB(db)
            tournament_service = TournamentServiceDB(db)
            sponsor_service = SponsorServiceDB(db)
            match_db_service = MatchDataServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_db_service = ScoreboardServiceDB(db)

            # Create all
            new_match = await self.service.create_or_update_match(data)

            default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
            default_playclock = PlayClockSchemaCreate(match_id=new_match.id)
            default_gameclock = GameClockSchemaCreate(match_id=new_match.id)

            tournament = await tournament_service.get_by_id(new_match.tournament_id)
            tournament_main_sponsor = await sponsor_service.get_by_id(tournament.main_sponsor_id)
            team_a = await teams_service.get_by_id(new_match.team_a_id)
            team_b = await teams_service.get_by_id(new_match.team_b_id)

            scale_main_sponsor = tournament_main_sponsor.scale_logo if tournament_main_sponsor else 2.0
            existing_scoreboard = await scoreboard_db_service.get_scoreboard_by_match_id(new_match.id)

            if existing_scoreboard is None:
                scoreboard_schema = ScoreboardSchemaCreate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=scale_main_sponsor,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title.title(),
                    team_b_game_title=team_b.title.title(),
                )
            else:
                scoreboard_schema = ScoreboardSchemaUpdate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=scale_main_sponsor,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title.title(),
                    team_b_game_title=team_b.title.title(),
                )
            new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(scoreboard_schema)

            new_match_data = await match_db_service.create_match_data(default_match_data)
            teams_data = await self.service.get_teams_by_match(new_match_data.match_id)
            new_playclock = await playclock_service.create_playclock(default_playclock)
            new_gameclock = await gameclock_service.create_gameclock(default_gameclock)

            return new_match.__dict__

        @router.post("/api/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_matches_endpoint(
                eesl_tournament_id: int,
        ):
            teams_service = TeamServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_service = ScoreboardServiceDB(db)
            tournament = await TournamentServiceDB(db).get_tournament_by_eesl_id(eesl_tournament_id)
            matches_list = await parse_tournament_matches_index_page_eesl(eesl_tournament_id)

            created_matches = []
            if matches_list:
                for m in matches_list:
                    team_a = await teams_service.get_team_by_eesl_id(m["team_a_id"])
                    team_b = await teams_service.get_team_by_eesl_id(m["team_b_id"])
                    match = {
                        "week": m["week"],
                        "match_eesl_id": m["match_eesl_id"],
                        "team_a_id": team_a.id,
                        "team_b_id": team_b.id,
                        "match_date": m["match_date"],
                        "tournament_id": tournament.id,
                    }
                    match_schema = MatchSchemaCreate(**match)
                    created_match = await self.service.create_or_update_match(match_schema)

                    playclock_schema = PlayClockSchemaCreate(match_id=created_match.id)
                    await playclock_service.create_playclock(playclock_schema)

                    gameclock_schema = GameClockSchemaCreate(match_id=created_match.id)
                    await gameclock_service.create_gameclock(gameclock_schema)

                    existing_scoreboard = await scoreboard_service.get_scoreboard_by_match_id(created_match.id)

                    if existing_scoreboard is None:
                        scoreboard_schema = ScoreboardSchemaCreate(
                            match_id=created_match.id,
                            scale_logo_a=2,
                            scale_logo_b=2,
                            team_a_game_color=team_a.team_color,
                            team_b_game_color=team_b.team_color,
                            team_a_game_title=team_a.title,
                            team_b_game_title=team_b.title,
                        )
                    else:
                        scoreboard_schema = ScoreboardSchemaUpdate(
                            match_id=created_match.id,
                            scale_logo_a=2,
                            scale_logo_b=2,
                            team_a_game_color=team_a.team_color,
                            team_b_game_color=team_b.team_color,
                            team_a_game_title=team_a.title,
                            team_b_game_title=team_b.title,
                        )
                    await scoreboard_service.create_or_update_scoreboard(scoreboard_schema)

                    created_matches.append(created_match)
                return created_matches
            else:
                return []

        return router


class MatchTemplateRouter(
    MinimalBaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/matches",
            ["matches"],
            service,
        )

    def route(self):
        router = super().route()

        @router.get(
            "/all/",
            response_class=HTMLResponse,
        )
        async def get_all_matches_endpoint(request: Request):
            template = templates.TemplateResponse(
                name="/matches/display/all-matches.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        @router.get(
            "/id/{match_id}/scoreboard/",
            response_class=HTMLResponse,
        )
        async def edit_match_data_endpoint(
                request: Request,
                match_id: int,
        ):
            template = templates.TemplateResponse(
                name="/scoreboards/display/score-main.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        @router.get(
            "/id/{match_id}/scoreboard/hd/",
            response_class=HTMLResponse,
        )
        async def display_fullhd_match_data_endpoint(
                request: Request,
                match_id: int,
        ):
            template = templates.TemplateResponse(
                name="/scoreboards/display/score-fullhd.html",
                context={
                    "request": request,
                },
                status_code=200,
            )
            return template

        return router


api_match_router = MatchAPIRouter(MatchServiceDB(db)).route()
template_match_router = MatchTemplateRouter(MatchServiceDB(db)).route()
