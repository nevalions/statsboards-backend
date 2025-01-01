import asyncio
import logging
from pprint import pprint
from typing import List, Annotated

from fastapi import HTTPException, Request, Depends, status, WebSocket, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.websockets import WebSocketDisconnect, WebSocketState
from websockets import ConnectionClosedOK

from src.core import BaseRouter, db, MinimalBaseRouter
from src.core.config import templates
from src.matchdata.db_services import MatchDataServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB
from .db_services import MatchServiceDB
from .shemas import (
    MatchSchemaCreate,
    MatchSchemaUpdate,
    MatchSchema,
)
from ..core.models.base import (
    ws_manager,
    connection_manager,
    ConnectionManager,
    process_client_queue,
)
from ..gameclocks.db_services import GameClockServiceDB
from ..gameclocks.schemas import GameClockSchemaCreate
from ..helpers.file_service import file_service
from ..logging_config import setup_logging, get_logger
from ..matchdata.schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from ..pars_eesl.pars_tournament import (
    parse_tournament_matches_index_page_eesl,
    ParsedMatchData,
)
from ..playclocks.db_services import PlayClockServiceDB
from ..playclocks.schemas import PlayClockSchemaCreate
from ..scoreboards.shemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from ..sponsors.db_services import SponsorServiceDB
from ..teams.db_services import TeamServiceDB
from ..teams.schemas import UploadTeamLogoResponse, UploadResizeTeamLogoResponse
from ..tournaments.db_services import TournamentServiceDB


setup_logging()
websocket_logger = logging.getLogger("backend_websocket_logger")
connection_socket_logger = logging.getLogger("backend_connection_socket_logger")


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
        self.logger = get_logger("backend_logger_MatchAPIRouter", self)
        self.logger.debug(f"Initialized MatchAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=MatchSchema,
        )
        async def create_match_endpoint(
            match: MatchSchemaCreate,
        ):
            self.logger.debug(f"Create or update match endpoint got data: {match}")
            new_match = await self.service.create_or_update_match(match)
            return new_match.__dict__

        @router.post(
            "/create_with_full_data/",
        )
        async def create_match_with_full_data_endpoint(
            data: MatchSchemaCreate,
        ):
            self.logger.debug(
                f"Create or update match with full data endpoint got data: {data}"
            )
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
            tournament_main_sponsor = await sponsor_service.get_by_id(
                tournament.main_sponsor_id
            )
            team_a = await teams_service.get_by_id(new_match.team_a_id)
            team_b = await teams_service.get_by_id(new_match.team_b_id)

            existing_scoreboard = (
                await scoreboard_db_service.get_scoreboard_by_match_id(new_match.id)
            )

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
            new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(
                scoreboard_schema
            )

            new_match_data = await match_db_service.create_match_data(
                default_match_data
            )
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
            self.logger.debug(f"Update match endpoint id:{item_id} data: {item}")
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
            self.logger.debug(f"Get match by eesl_id endpoint got eesl_id:{eesl_id}")
            match = await self.service.get_match_by_eesl_id(value=eesl_id)
            if match is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match eesl_id({eesl_id}) " f"not found",
                )
            return match.__dict__

        @router.get(
            "/id/{match_id}/sport/",
        )
        async def get_match_sport_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sport by match id:{match_id} endpoint")
            return await self.service.get_sport_by_match_id(match_id)

        @router.get(
            "/id/{match_id}/teams/",
        )
        async def get_match_teams_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sport by match id:{match_id} endpoint")
            return await self.service.get_teams_by_match(match_id)

        @router.get(
            "/id/{match_id}/home_away_teams/",
        )
        async def get_match_home_away_teams_by_match_id_endpoint(match_id: int):
            self.logger.debug(
                f"Get match home and away teams by match id:{match_id} endpoint"
            )
            return await self.service.get_teams_by_match_id(match_id)

        @router.get("/id/{match_id}/players/")
        async def get_players_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get players by match id:{match_id} endpoint")
            return await self.service.get_players_by_match(match_id)

        @router.get("/id/{match_id}/players_fulldata/")
        async def get_players_with_full_data_by_match_id_endpoint(match_id: int):
            self.logger.debug(
                f"Get players with full data by match id:{match_id} endpoint"
            )
            return await self.service.get_player_by_match_full_data(match_id)

        @router.get("/id/{match_id}/sponsor_line")
        async def get_sponsor_line_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sponsor_line by match id:{match_id} endpoint")
            sponsor_line = await self.service.get_match_sponsor_line(match_id)
            if sponsor_line:
                full_sponsor_line = await SponsorSponsorLineServiceDB(
                    db
                ).get_related_sponsors(sponsor_line.id)
                return full_sponsor_line

        @router.get(
            "/id/{match_id}/match_data/",
        )
        async def get_match_data_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get matchdata by match id:{match_id} endpoint")
            return await self.service.get_matchdata_by_match(match_id)

        @router.get(
            "/id/{match_id}/playclock/",
        )
        async def get_playclock_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get playclock by match id:{match_id} endpoint")
            return await self.service.get_playclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/gameclock/",
        )
        async def get_gameclock_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get gameclock by match id:{match_id} endpoint")
            return await self.service.get_gameclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard_data/",
        )
        async def get_match_scoreboard_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get scoreboard_data by match id:{match_id} endpoint")
            return await self.service.get_scoreboard_by_match(match_id)

        @router.get("/all/data/", response_class=JSONResponse)
        async def all_matches_data_endpoint_endpoint(
            all_matches: List = Depends(self.service.get_all_elements),
        ):
            from src.helpers.fetch_helpers import fetch_list_of_matches_data

            self.logger.debug(f"Get all match data by match endpoint")
            return await fetch_list_of_matches_data(all_matches)

        @router.get(
            "/id/{match_id}/data/",
            response_class=JSONResponse,
        )
        async def match_data_endpoint(
            match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
            match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            self.logger.debug(f"Get teams and match data by match endpoint")
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

            self.logger.debug(f"Get full_match_data by match endpoint")
            return await fetch_match_data(match_id)

        @router.get(
            "/id/{match_id}/scoreboard/full_data/scoreboard_settings/",
            response_class=JSONResponse,
        )
        async def full_match_data_with_scoreboard_endpoint(match_id: int):
            self.logger.debug(f"Get full_match_data_with_scoreboard by match endpoint")
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            return await fetch_with_scoreboard_data(match_id)

        @router.post(
            "/id/{match_id}/upload_team_logo", response_model=UploadTeamLogoResponse
        )
        async def upload_team_logo(match_id: int, file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(
                file, sub_folder=f"match/{match_id}/teams_logos"
            )
            self.logger.debug(
                f"Upload team in match logo endpoint file location: {file_location}"
            )
            return {"logoUrl": file_location}

        @router.post(
            "/id/{match_id}/upload_resize_logo",
            response_model=UploadResizeTeamLogoResponse,
        )
        async def upload_resize_team_logo(match_id: int, file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder=f"match/{match_id}/teams_logos",
                icon_height=100,
                web_view_height=400,
            )
            self.logger.debug(
                f"Upload and resize team in match logo endpoint file location: {uploaded_paths}"
            )
            return uploaded_paths

        async def get_connection_manager() -> ConnectionManager:
            return connection_manager

        @router.websocket("/ws/id/{match_id}/{client_id}/")
        async def websocket_endpoint(
            websocket: WebSocket,
            client_id: str,
            match_id: int,
        ):
            websocket_logger.debug(
                f"Websocket endpoint /ws/id/{match_id}/{client_id} {websocket} "
            )
            await websocket.accept()
            # connection_socket_logger.debug(f"Connection Manager {match_id}")
            await connection_manager.connect(websocket, client_id, match_id)
            await ws_manager.connect(client_id)

            try:
                from src.helpers.fetch_helpers import (
                    fetch_with_scoreboard_data,
                    fetch_playclock,
                    fetch_gameclock,
                )

                type_message_update = "message-update"
                initial_data = await fetch_with_scoreboard_data(match_id)
                initial_data["type"] = type_message_update
                websocket_logger.debug(
                    f"WebSocket Connection initial_data for type: {type_message_update}"
                )
                websocket_logger.info(
                    f"WebSocket Connection initial_data: {initial_data}"
                )

                type_playclock_update = "playclock-update"
                initial_playclock_data = await fetch_playclock(match_id)
                initial_playclock_data["type"] = type_playclock_update
                websocket_logger.debug(
                    f"WebSocket Connection initial_data for type: {type_playclock_update}"
                )
                websocket_logger.info(
                    f"WebSocket Connection initial_data: {initial_playclock_data}"
                )

                type_gameclock_update = "gameclock-update"
                initial_gameclock_data = await fetch_gameclock(match_id)
                initial_gameclock_data["type"] = type_gameclock_update
                websocket_logger.debug(
                    f"WebSocket Connection initial_data for type: {type_gameclock_update}"
                )
                websocket_logger.info(
                    f"WebSocket Connection initial_data: {initial_gameclock_data}"
                )

                await websocket.send_json(initial_data)
                await websocket.send_json(initial_playclock_data)
                await websocket.send_json(initial_gameclock_data)

                # Ensure the client_id is associated with a queue
                if client_id in connection_manager.queues:
                    # Add the data to the client's queue
                    await connection_manager.queues[client_id].put(initial_data)
                    await connection_manager.queues[client_id].put(
                        initial_playclock_data
                    )
                    await connection_manager.queues[client_id].put(
                        initial_gameclock_data
                    )
                    websocket_logger.debug(
                        f"Put initial_data into queue for client_id:{client_id}: {initial_data}"
                    )
                    websocket_logger.debug(
                        f"Put initial_playclock_data into queue for client_id:{client_id}: {initial_playclock_data}"
                    )
                    websocket_logger.debug(
                        f"Put initial_gameclock_data into queue for client_id:{client_id}: {initial_gameclock_data}"
                    )
                else:
                    websocket_logger.warning(
                        f"No queue found for client_id {client_id}. Data not enqueued."
                    )

                await process_data_websocket(websocket, client_id, match_id)

            except WebSocketDisconnect as e:
                websocket_logger.error(
                    f"WebSocket disconnect error:{str(e)}", exc_info=True
                )
            except ConnectionClosedOK as e:
                websocket_logger.error(
                    f"ConnectionClosedOK error:{str(e)}", exc_info=True
                )
            except asyncio.TimeoutError as e:
                websocket_logger.error(f"TimeoutError error:{str(e)}", exc_info=True)
            except RuntimeError as e:
                websocket_logger.error(f"RuntimeError error:{str(e)}", exc_info=True)
            except Exception as e:
                websocket_logger.error(f"Unexpected error:{str(e)}", exc_info=True)
            finally:
                await connection_manager.disconnect(client_id)
                connection_socket_logger.warning(
                    f"Client {client_id} disconnected, closing connection "
                    f"and removing from subscriptions"
                )
                await ws_manager.disconnect(client_id)
                websocket_logger.warning(
                    f"Client {client_id} disconnected from websocket, closing connection"
                )

        async def process_data_websocket(
            websocket: WebSocket, client_id: str, match_id: int
        ):
            websocket_logger.debug(f"WebSocketState: {websocket.application_state}")
            handlers = {
                "message-update": process_match_data,
                "gameclock-update": process_gameclock_data,
                "playclock-update": process_playclock_data,
                "matchdata": process_match_data,
                "gameclock": process_gameclock_data,
                "playclock": process_playclock_data,
                "match": process_match_data,
                "scoreboard": process_match_data,
            }
            websocket_logger.debug(f"Process data websocket handlers: {handlers}")
            websocket_logger.debug(f"WebSocketState: {websocket.application_state}")

            while websocket.application_state == WebSocketState.CONNECTED:
                print(f"WebSocketState: {websocket.application_state}")
                print(f"Process data websocket for client_id: {client_id}")

                data = await connection_manager.get_queue_for_client(client_id)
                connection_socket_logger.debug(f"DATAAAAAAAAAAAAA: {data}")
                # message_data = data.get("data")
                message_type = data.get("type")  # Extract the message type

                if message_type in handlers:
                    print(f"Message received for type: {message_type}")
                    await handlers[message_type](websocket, match_id)
                    print(f"Message data: {data}")
                else:
                    print(f"Unknown message type: {message_type}")

                # data = await connection_manager.get_queue_for_client(client_id)
                # if data:
                #     # print(f"Message for client {client_id}: {message}")
                #     await process_client_queue(client_id, handlers)
                # else:
                #     print(f"NO MESSAGE")

            # if data:
            #     try:
            #         # Add a timeout to prevent indefinite blocking
            #         message = await asyncio.wait_for(data.get(), timeout=3.0)
            #         # print(f"Message for client {client_id}: {message}")
            #         # connection_socket_logger.critical(f'TABLE: {data.get("table")}')
            #         connection_socket_logger.critical(
            #             f"Message for client {client_id}: {message}"
            #         )
            #     except asyncio.TimeoutError:
            #         # print(
            #         #     f"No messages in the queue for client {client_id} within timeout."
            #         # )
            #         connection_socket_logger.warning(
            #             f"No messages in the queue for client {client_id} within timeout."
            #         )
            #         await connection_manager.connect(websocket, client_id, match_id)
            #         data = await connection_manager.get_queue_for_client(client_id)
            #         new_massage = await data.get()
            #         connection_socket_logger.critical(
            #             f"NEW Message for client {client_id}: {new_massage}"
            #         )

            # data = await connection_manager.queues[client_id].get()
            # websocket_logger.debug(
            #     f"Process websocket data: {data} for client_id: {client_id}"
            # )
            # handler = handlers.get(data)
            # websocket_logger.debug(f"Process websocket handler: {handler}")
            # if not handler:
            #     websocket_logger.warning(f"No handler for table {data}")
            #     continue
            # try:
            #     await handler(websocket, match_id)
            # except Exception as e:
            #     websocket_logger.error(
            #         f'Websocket handler error for client {client_id}, table {data.get("table")}: {e}'
            #     )

        async def process_match_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            full_match_data = await fetch_with_scoreboard_data(match_id)
            full_match_data["type"] = "match-update"
            print("[WebSocket Connection] Full match data fetched: ", full_match_data)
            await websocket.send_json(full_match_data)

        async def process_gameclock_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_gameclock

            gameclock_data = await fetch_gameclock(match_id)
            gameclock_data["type"] = "gameclock-update"
            print("[WebSocket Connection] Gameclock data fetched: ", gameclock_data)
            await websocket.send_json(gameclock_data)

        async def process_playclock_data(websocket: WebSocket, match_id):
            from src.helpers.fetch_helpers import fetch_playclock

            playclock_data = await fetch_playclock(match_id)
            playclock_data["type"] = "playclock-update"
            print("[WebSocket Connection] Playclock data fetched: ", playclock_data)
            await websocket.send_json(playclock_data)

        @router.get(
            "/pars/tournament/{eesl_tournament_id}",
            # response_model=List[MatchSchemaCreate],
        )
        async def get_parse_tournament_matches(eesl_tournament_id: int):
            return await parse_tournament_matches_index_page_eesl(eesl_tournament_id)

        @router.post("/add")
        async def create_match_with_full_data_and_scoreboard_endpoint(
            data: MatchSchemaCreate,
        ):
            self.logger.debug(
                f"Creat match with full data and scoreboard endpoint {data}"
            )
            teams_service = TeamServiceDB(db)
            tournament_service = TournamentServiceDB(db)
            sponsor_service = SponsorServiceDB(db)
            match_db_service = MatchDataServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_db_service = ScoreboardServiceDB(db)

            # Create all
            self.logger.debug(f"Creating simple match: {data}")
            new_match = await self.service.create_or_update_match(data)

            self.logger.debug(f"Creating default matchdata, playclock and gameclock")
            default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
            default_playclock = PlayClockSchemaCreate(match_id=new_match.id)
            default_gameclock = GameClockSchemaCreate(match_id=new_match.id)

            tournament = await tournament_service.get_by_id(new_match.tournament_id)
            tournament_main_sponsor = await sponsor_service.get_by_id(
                tournament.main_sponsor_id
            )
            team_a = await teams_service.get_by_id(new_match.team_a_id)
            team_b = await teams_service.get_by_id(new_match.team_b_id)

            scale_main_sponsor = (
                tournament_main_sponsor.scale_logo if tournament_main_sponsor else 2.0
            )
            existing_scoreboard = (
                await scoreboard_db_service.get_scoreboard_by_match_id(new_match.id)
            )

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
            new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(
                scoreboard_schema
            )

            new_match_data = await match_db_service.create_match_data(
                default_match_data
            )
            teams_data = await self.service.get_teams_by_match(new_match_data.match_id)
            new_playclock = await playclock_service.create_playclock(default_playclock)
            new_gameclock = await gameclock_service.create_gameclock(default_gameclock)
            self.logger.info(
                f"Created match with full data and scoreboard {new_match.__dict__}"
            )
            return new_match.__dict__

        @router.get("/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_matches_endpoint(
            eesl_tournament_id: int,
        ):
            self.logger.debug(
                f"Get and Save parsed matches from tournament eesl_id:{eesl_tournament_id} endpoint"
            )
            teams_service = TeamServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_service = ScoreboardServiceDB(db)
            match_data_service = MatchDataServiceDB(db)
            tournament = await TournamentServiceDB(db).get_tournament_by_eesl_id(
                eesl_tournament_id
            )
            matches_list: List[
                ParsedMatchData
            ] = await parse_tournament_matches_index_page_eesl(eesl_tournament_id)

            created_matches = []
            created_matches_full_data = []

            if matches_list:
                for m in matches_list:
                    try:
                        self.logger.debug(f"Parsed match: {m}")
                        team_a = await teams_service.get_team_by_eesl_id(
                            m["team_a_eesl_id"]
                        )
                        if team_a:
                            self.logger.debug(f"team_a: {team_a}")
                        else:
                            self.logger.error(f"Home team(a) not found")
                            raise
                        team_b = await teams_service.get_team_by_eesl_id(
                            m["team_b_eesl_id"]
                        )
                        if team_b:
                            self.logger.debug(f"team_a: {team_b}")
                        else:
                            self.logger.error(f"Away team(b) not found")
                            raise
                        match = {
                            "week": m["week"],
                            "match_eesl_id": m["match_eesl_id"],
                            "team_a_id": team_a.id,
                            "team_b_id": team_b.id,
                            "match_date": m["match_date"],
                            "tournament_id": tournament.id,
                        }
                        match_schema = MatchSchemaCreate(**match)
                        created_match = await self.service.create_or_update_match(
                            match_schema
                        )

                        playclock_schema = PlayClockSchemaCreate(
                            match_id=created_match.id
                        )
                        await playclock_service.create_playclock(playclock_schema)

                        gameclock_schema = GameClockSchemaCreate(
                            match_id=created_match.id
                        )
                        await gameclock_service.create_gameclock(gameclock_schema)

                        existing_match_data = (
                            await match_data_service.get_match_data_by_match_id(
                                created_match.id
                            )
                        )

                        if existing_match_data is None:
                            match_data_schema_create = MatchDataSchemaCreate(
                                match_id=created_match.id,
                                score_team_a=m["score_team_a"],
                                score_team_b=m["score_team_b"],
                            )
                            match_data = await match_data_service.create_match_data(
                                match_data_schema_create
                            )
                            # print("match_data", match_data)
                        else:
                            match_data_schema_update = MatchDataSchemaUpdate(
                                match_id=created_match.id,
                                score_team_a=m["score_team_a"],
                                score_team_b=m["score_team_b"],
                            )
                            match_data = await match_data_service.update_match_data(
                                existing_match_data.id, match_data_schema_update
                            )
                            # print("match_data", match_data)

                        existing_scoreboard = (
                            await scoreboard_service.get_scoreboard_by_match_id(
                                created_match.id
                            )
                        )

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
                            # Update existing_scoreboard with default values where keys are missing
                            existing_data = existing_scoreboard.__dict__
                            default_data = ScoreboardSchemaCreate().model_dump()

                            for key, value in default_data.items():
                                if (
                                    key not in existing_data
                                    or existing_data[key] is None
                                ):
                                    existing_data[key] = value

                            scoreboard_schema = ScoreboardSchemaUpdate(**existing_data)

                        created_scoreboard = (
                            await scoreboard_service.create_or_update_scoreboard(
                                scoreboard_schema
                            )
                        )

                        teams_data = await self.service.get_teams_by_match(
                            created_match.id
                        )

                        created_matches.append(created_match)
                        created_matches_full_data.append(
                            {
                                "id": created_match.id,
                                "match_id": created_match.id,
                                "status_code": 200,
                                "match": created_match,
                                "teams_data": teams_data,
                                "match_data": match_data,
                                "scoreboard_data": created_scoreboard,
                            }
                        )

                        self.logger.info(
                            f"Created matches with full data after parsing: {created_matches_full_data}"
                        )
                    except Exception as ex:
                        self.logger.error(
                            f"Error on parse and create matches from tournament: {ex}",
                            exc_info=True,
                        )

                return created_matches_full_data
            else:
                self.logger.warning(f"Matches list is empty")
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
