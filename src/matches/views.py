import asyncio
import logging
from typing import List

from fastapi import Depends, File, HTTPException, Request, UploadFile, WebSocket, status
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.websockets import WebSocketDisconnect, WebSocketState
from websockets import ConnectionClosedError, ConnectionClosedOK

from src.core import BaseRouter, MinimalBaseRouter, db
from src.core.config import templates
from src.matchdata.db_services import MatchDataServiceDB
from src.scoreboards.db_services import ScoreboardServiceDB
from src.sponsor_sponsor_line_connection.db_services import SponsorSponsorLineServiceDB

from ..core.models.base import (
    connection_manager,
    ws_manager,
)
from ..gameclocks.db_services import GameClockServiceDB
from ..gameclocks.schemas import GameClockSchemaCreate
from ..helpers.file_service import file_service
from ..logging_config import get_logger, setup_logging
from ..matchdata.schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate
from ..pars_eesl.pars_tournament import (
    ParsedMatchData,
    parse_tournament_matches_index_page_eesl,
)
from ..playclocks.db_services import PlayClockServiceDB
from ..playclocks.schemas import PlayClockSchemaCreate
from ..scoreboards.schemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from ..sponsors.db_services import SponsorServiceDB
from ..teams.db_services import TeamServiceDB
from ..teams.schemas import UploadResizeTeamLogoResponse, UploadTeamLogoResponse
from ..tournaments.db_services import TournamentServiceDB
from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)

setup_logging()
websocket_logger = logging.getLogger("backend_logger_MatchDataWebSocketManager")
connection_socket_logger = logging.getLogger("backend_logger_ConnectionManager")


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
        self.logger.debug("Initialized MatchAPIRouter")

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
            if new_match:
                return MatchSchema.model_validate(new_match)
            else:
                self.logger.error(f"Error creating match with data: {match}")
                raise HTTPException(status_code=409, detail="Match creation fail")

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

            new_match_data = await match_db_service.create(default_match_data)
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
            try:
                match_update = await self.service.update(item_id, item)
                return MatchSchema.model_validate(match_update)
            except HTTPException:
                raise

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
                    detail=f"Match eesl_id({eesl_id}) not found",
                )
            return MatchSchema.model_validate(match)

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

            self.logger.debug("Get all match data by match endpoint")
            return await fetch_list_of_matches_data(all_matches)

        @router.get(
            "/id/{match_id}/data/",
            response_class=JSONResponse,
        )
        async def match_data_endpoint(
            match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
            match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            self.logger.debug("Get teams and match data by match endpoint")
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

            self.logger.debug("Get full_match_data by match endpoint")
            return await fetch_match_data(match_id)

        @router.get(
            "/id/{match_id}/scoreboard/full_data/scoreboard_settings/",
            response_class=JSONResponse,
        )
        async def full_match_data_with_scoreboard_endpoint(match_id: int):
            self.logger.debug("Get full_match_data_with_scoreboard by match endpoint")
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

        async def _send_initial_data(
            websocket: WebSocket, client_id: str, match_id: int
        ):
            from src.helpers.fetch_helpers import (
                fetch_gameclock,
                fetch_playclock,
                fetch_with_scoreboard_data,
            )

            initial_data = await fetch_with_scoreboard_data(match_id)
            initial_data["type"] = "message-update"
            websocket_logger.debug(
                "WebSocket Connection initial_data for type: message-update"
            )
            websocket_logger.info(f"WebSocket Connection initial_data: {initial_data}")

            initial_playclock_data = await fetch_playclock(match_id)
            initial_playclock_data["type"] = "playclock-update"
            websocket_logger.debug(
                "WebSocket Connection initial_data for type: playclock-update"
            )
            websocket_logger.info(
                f"WebSocket Connection initial_data: {initial_playclock_data}"
            )

            initial_gameclock_data = await fetch_gameclock(match_id)
            initial_gameclock_data["type"] = "gameclock-update"
            websocket_logger.debug(
                "WebSocket Connection initial_data for type: gameclock-update"
            )
            websocket_logger.info(
                f"WebSocket Connection initial_data: {initial_gameclock_data}"
            )

            await websocket.send_json(initial_data)
            await websocket.send_json(initial_playclock_data)
            await websocket.send_json(initial_gameclock_data)

            if client_id in connection_manager.queues:
                await connection_manager.queues[client_id].put(initial_data)
                await connection_manager.queues[client_id].put(initial_playclock_data)
                await connection_manager.queues[client_id].put(initial_gameclock_data)
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

        async def _cleanup_websocket(client_id: str):
            await asyncio.sleep(0.1)
            await connection_manager.disconnect(client_id)
            connection_socket_logger.warning(
                f"Client {client_id} disconnected, closing connection and removing from subscriptions"
            )
            await ws_manager.disconnect(client_id)
            websocket_logger.warning(
                f"Client {client_id} disconnected from websocket, closing connection"
            )
            await ws_manager.shutdown()

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
            await connection_manager.connect(websocket, client_id, match_id)
            await ws_manager.startup()

            try:
                await _send_initial_data(websocket, client_id, match_id)
                await process_data_websocket(websocket, client_id, match_id)

            except WebSocketDisconnect as e:
                websocket_logger.error(
                    f"WebSocket disconnect error:{str(e)}", exc_info=True
                )
            except ConnectionClosedOK as e:
                websocket_logger.debug(
                    f"ConnectionClosedOK error:{str(e)}", exc_info=True
                )
            except asyncio.TimeoutError as e:
                websocket_logger.error(f"TimeoutError error:{str(e)}", exc_info=True)
            except RuntimeError as e:
                websocket_logger.error(f"RuntimeError error:{str(e)}", exc_info=True)
            except Exception as e:
                websocket_logger.error(f"Unexpected error:{str(e)}", exc_info=True)
            finally:
                await _cleanup_websocket(client_id)

        async def process_data_websocket(
            websocket: WebSocket, client_id: str, match_id: int
        ):
            websocket_logger.debug(f"WebSocketState: {websocket.application_state}")
            handlers = {
                "message-update": process_match_data,
                "match-update": process_match_data,
                "gameclock-update": process_gameclock_data,
                "playclock-update": process_playclock_data,
                "matchdata": process_match_data,
                "gameclock": process_gameclock_data,
                "playclock": process_playclock_data,
                "match": process_match_data,
                "scoreboard": process_match_data,
            }

            while True:
                if websocket.application_state != WebSocketState.CONNECTED:
                    websocket_logger.warning(
                        f"WebSocket disconnected (state: {websocket.application_state}), ending processing loop"
                    )
                    break

                try:
                    queue = await connection_manager.get_queue_for_client(client_id)
                    timeout_ = 60.0 * 60 * 12  # hours

                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=timeout_)

                        if not isinstance(data, dict):
                            websocket_logger.warning(
                                f"Received non-dictionary data: {data}"
                            )
                            continue

                        message_type = data.get("type")
                        if message_type not in handlers:
                            websocket_logger.warning(
                                f"Unknown message type received: {message_type}"
                            )
                            continue

                        if websocket.application_state == WebSocketState.CONNECTED:
                            await handlers[message_type](websocket, match_id)
                        else:
                            websocket_logger.warning(
                                "WebSocket disconnected, stopping message processing"
                            )
                            break

                    except asyncio.TimeoutError:
                        websocket_logger.debug(
                            f"Queue get operation timed out after {timeout_ / 60 / 60} hours"
                        )
                        break

                except Exception as e:
                    websocket_logger.error(
                        f"Error in processing loop: {e}", exc_info=True
                    )
                    break

        async def process_match_data(websocket: WebSocket, match_id: int):
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            try:
                # Check connection state before fetching data
                if websocket.application_state != WebSocketState.CONNECTED:
                    websocket_logger.warning(
                        "WebSocket not connected, skipping data send"
                    )
                    return

                full_match_data = await fetch_with_scoreboard_data(match_id)
                full_match_data["type"] = "match-update"

                # Double check connection state before sending
                if websocket.application_state == WebSocketState.CONNECTED:
                    websocket_logger.debug(
                        f"Processing match data type: {full_match_data['type']}"
                    )
                    websocket_logger.debug(f"Match data fetched: {full_match_data}")
                    try:
                        await websocket.send_json(full_match_data)
                    except ConnectionClosedOK:
                        websocket_logger.debug(
                            "WebSocket closed normally while sending data"
                        )
                    except ConnectionClosedError as e:
                        websocket_logger.error(
                            f"WebSocket closed with error while sending data: {e}"
                        )
                else:
                    websocket_logger.warning(
                        f"WebSocket no longer connected (state: {websocket.application_state}), skipping data send"
                    )

            except Exception as e:
                websocket_logger.error(
                    f"Error processing match data: {e}", exc_info=True
                )

        async def process_gameclock_data(websocket: WebSocket, match_id: int):
            from src.helpers.fetch_helpers import fetch_gameclock

            try:
                # Check connection state before fetching data
                if websocket.application_state != WebSocketState.CONNECTED:
                    websocket_logger.warning(
                        "WebSocket not connected, skipping gameclock data send"
                    )
                    return

                gameclock_data = await fetch_gameclock(match_id)
                gameclock_data["type"] = "gameclock-update"

                # Double check connection state before sending
                if websocket.application_state == WebSocketState.CONNECTED:
                    websocket_logger.debug(
                        f"Processing match data type: {gameclock_data['type']}"
                    )
                    websocket_logger.debug(f"Gameclock data fetched: {gameclock_data}")
                    try:
                        await websocket.send_json(gameclock_data)
                    except ConnectionClosedOK:
                        websocket_logger.debug(
                            "WebSocket closed normally while sending gameclock data"
                        )
                    except ConnectionClosedError as e:
                        websocket_logger.error(
                            f"WebSocket closed with error while sending gameclock data: {e}"
                        )
                else:
                    websocket_logger.warning(
                        f"WebSocket no longer connected (state: {websocket.application_state}), skipping gameclock data send"
                    )
            except Exception as e:
                websocket_logger.error(
                    f"Error processing gameclock data: {e}", exc_info=True
                )

        async def process_playclock_data(websocket: WebSocket, match_id: int):
            from src.helpers.fetch_helpers import fetch_playclock

            try:
                # Check connection state before fetching data
                if websocket.application_state != WebSocketState.CONNECTED:
                    websocket_logger.warning(
                        "WebSocket not connected, skipping playclock data send"
                    )
                    return

                playclock_data = await fetch_playclock(match_id)
                playclock_data["type"] = "playclock-update"

                # Double check connection state before sending
                if websocket.application_state == WebSocketState.CONNECTED:
                    websocket_logger.debug(
                        f"Processing match data type: {playclock_data['type']}"
                    )
                    websocket_logger.debug(f"Playclock data fetched: {playclock_data}")
                    try:
                        await websocket.send_json(playclock_data)
                    except ConnectionClosedOK:
                        websocket_logger.debug(
                            "WebSocket closed normally while sending playclock data"
                        )
                    except ConnectionClosedError as e:
                        websocket_logger.error(
                            f"WebSocket closed with error while sending playclock data: {e}"
                        )
                else:
                    websocket_logger.warning(
                        f"WebSocket no longer connected (state: {websocket.application_state}), skipping playclock data send"
                    )
            except Exception as e:
                websocket_logger.error(
                    f"Error processing playclock data: {e}", exc_info=True
                )

        # async def process_data_websocket(
        #     websocket: WebSocket, client_id: str, match_id: int
        # ):
        #     websocket_logger.debug(f"WebSocketState: {websocket.application_state}")
        #     handlers = {
        #         "message-update": process_match_data,
        #         "match-update": process_match_data,
        #         "gameclock-update": process_gameclock_data,
        #         "playclock-update": process_playclock_data,
        #         "matchdata": process_match_data,
        #         "gameclock": process_gameclock_data,
        #         "playclock": process_playclock_data,
        #         "match": process_match_data,
        #         "scoreboard": process_match_data,
        #     }
        #     websocket_logger.debug(f"Process data websocket handlers: {handlers}")
        #     websocket_logger.debug(f"WebSocketState: {websocket.application_state}")
        #
        #     while websocket.application_state == WebSocketState.CONNECTED:
        #         websocket_logger.debug(
        #             f"Process data websocket for client_id: {client_id}"
        #         )
        #
        #         # Get the client's queue
        #         queue = await connection_manager.get_queue_for_client(client_id)
        #         timeout_ = 60.0 * 60 * 12  # hours
        #         try:
        #             data = await asyncio.wait_for(queue.get(), timeout=timeout_)
        #             websocket_logger.debug(f"Received data from queue: {data}")
        #             active_connections = (
        #                 await connection_manager.get_active_connections()
        #             )
        #
        #             if isinstance(data, dict):
        #                 message_type = data.get("type")
        #
        #                 if message_type in handlers:
        #                     websocket_logger.debug(
        #                         f"Processing message type: {message_type}"
        #                     )
        #                     try:
        #                         await handlers[message_type](websocket, match_id)
        #                         websocket_logger.debug(
        #                             f"Successfully processed message: {data}"
        #                         )
        #                     except Exception as e:
        #                         websocket_logger.error(
        #                             f"Error processing message: {str(e)}", exc_info=True
        #                         )
        #                 else:
        #                     websocket_logger.warning(
        #                         f"Unknown message type received: {message_type}"
        #                     )
        #             else:
        #                 websocket_logger.warning(
        #                     f"Received non-dictionary data: {data}"
        #                 )
        #
        #             for queue_type, queue_dict in [
        #                 ("match", ws_manager.match_data_queues),
        #                 ("playclock", ws_manager.playclock_queues),
        #                 ("gameclock", ws_manager.gameclock_queues),
        #             ]:
        #                 self.logger.debug(f"queue dict: {queue_dict}")
        #                 self.logger.debug(f"active connections: {active_connections}")
        #                 if client_id in active_connections:
        #                     connection_socket_logger.info(
        #                         f"Client id:{client_id} in queue:{active_connections}"
        #                     )
        #                     try:
        #                         # queue_data = queue_dict[client_id].get_nowait()
        #                         if queue_type == "match":
        #                             await process_match_data(websocket, match_id)
        #                         elif queue_type == "playclock":
        #                             await process_playclock_data(websocket, match_id)
        #                         elif queue_type == "gameclock":
        #                             await process_gameclock_data(websocket, match_id)
        #                     except asyncio.QueueEmpty:
        #                         continue
        #                     except Exception as e:
        #                         websocket_logger.error(
        #                             f"Error processing {queue_type} queue: {str(e)}",
        #                             exc_info=True,
        #                         )
        #                 else:
        #                     connection_socket_logger.error(
        #                         f"Client {client_id} not in {active_connections}"
        #                     )
        #                     break
        #
        #         except asyncio.TimeoutError:
        #             websocket_logger.debug(
        #                 f"Queue get operation timed out {timeout_/60/60} hours, breaks..."
        #             )
        #             break
        #         except Exception as e:
        #             websocket_logger.error(
        #                 f"Error getting message from queue, breaks: {e}",
        #                 exc_info=True,
        #             )
        #             break
        #
        # async def process_match_data(websocket: WebSocket, match_id: int):
        #     from src.helpers.fetch_helpers import fetch_with_scoreboard_data
        #
        #     try:
        #         full_match_data = await fetch_with_scoreboard_data(match_id)
        #         full_match_data["type"] = "match-update"
        #         websocket_logger.debug(
        #             f"Processing match data type: {full_match_data['type']}"
        #         )
        #         websocket_logger.debug(f"Match data fetched: {full_match_data}")
        #         websocket_logger.debug(
        #             f"websocket status: {websocket.application_state}"
        #         )
        #         await websocket.send_json(full_match_data)
        #     except Exception as e:
        #         websocket_logger.error(
        #             f"Error processing match data: {e}", exc_info=True
        #         )
        #
        # async def process_gameclock_data(websocket: WebSocket, match_id: int):
        #     from src.helpers.fetch_helpers import fetch_gameclock
        #
        #     try:
        #         gameclock_data = await fetch_gameclock(match_id)
        #         gameclock_data["type"] = "gameclock-update"
        #         websocket_logger.debug(
        #             f"Processing match data type: {gameclock_data['type']}"
        #         )
        #         websocket_logger.debug(f"Gameclock data fetched: {gameclock_data}")
        #         await websocket.send_json(gameclock_data)
        #     except Exception as e:
        #         websocket_logger.error(
        #             f"Error processing gameclock data: {e}", exc_info=True
        #         )
        #
        # async def process_playclock_data(websocket: WebSocket, match_id: int):
        #     from src.helpers.fetch_helpers import fetch_playclock
        #
        #     try:
        #         playclock_data = await fetch_playclock(match_id)
        #         playclock_data["type"] = "playclock-update"
        #         websocket_logger.debug(
        #             f"Processing match data type: {playclock_data['type']}"
        #         )
        #         websocket_logger.debug(f"Playclock data fetched: {playclock_data}")
        #         await websocket.send_json(playclock_data)
        #     except Exception as e:
        #         websocket_logger.error(
        #             f"Error processing playclock data: {e}", exc_info=True
        #         )

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
            try:
                self.logger.debug(f"Creating simple match: {data}")
                new_match = await self.service.create_or_update_match(data)

                self.logger.debug("Creating default matchdata, playclock and gameclock")
                default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
                default_playclock = PlayClockSchemaCreate(match_id=new_match.id)
                default_gameclock = GameClockSchemaCreate(match_id=new_match.id)

                self.logger.debug("Get tournament and tournament main sponsor")
                tournament = await tournament_service.get_by_id(new_match.tournament_id)
                tournament_main_sponsor = await sponsor_service.get_by_id(
                    tournament.main_sponsor_id
                )
                self.logger.debug("Get teams for match")
                team_a = await teams_service.get_by_id(new_match.team_a_id)
                team_b = await teams_service.get_by_id(new_match.team_b_id)

                scale_main_sponsor = (
                    tournament_main_sponsor.scale_logo
                    if tournament_main_sponsor
                    else 2.0
                )
                self.logger.debug("If scoreboard exist")
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
                new_scoreboard = (
                    await scoreboard_db_service.create_or_update_scoreboard(
                        scoreboard_schema
                    )
                )
                self.logger.debug(
                    f"Scoreboard created or updated: {new_scoreboard.__dict__}"
                )

                new_match_data = await match_db_service.create(default_match_data)
                teams_data = await self.service.get_teams_by_match(
                    new_match_data.match_id
                )
                new_playclock = await playclock_service.create(default_playclock)
                new_gameclock = await gameclock_service.create(default_gameclock)
                self.logger.info(
                    f"Created match with full data and scoreboard {MatchSchema.model_validate(new_match)}"
                )
                return MatchSchema.model_validate(new_match)
            except Exception as e:
                self.logger.error(
                    f"Error creating match with full data and scoreboard: {str(e)}",
                    exc_info=True,
                )

        @router.get("/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_matches_endpoint(
            eesl_tournament_id: int,
        ):
            self.logger.debug(
                f"Get and Save parsed matches from tournament eesl_id:{eesl_tournament_id} endpoint"
            )
            from sqlalchemy import select
            from src.core.models import TeamDB

            teams_service = TeamServiceDB(db)
            playclock_service = PlayClockServiceDB(db)
            gameclock_service = GameClockServiceDB(db)
            scoreboard_service = ScoreboardServiceDB(db)
            match_data_service = MatchDataServiceDB(db)
            tournament = await TournamentServiceDB(db).get_tournament_by_eesl_id(
                eesl_tournament_id
            )
            try:
                self.logger.debug("Start parsing tournament for matches")
                matches_list: List[
                    ParsedMatchData
                ] = await parse_tournament_matches_index_page_eesl(eesl_tournament_id)

                created_matches = []
                created_matches_full_data = []

                if matches_list:
                    team_eesl_ids = set()
                    for m in matches_list:
                        team_eesl_ids.add(m["team_a_eesl_id"])
                        team_eesl_ids.add(m["team_b_eesl_id"])

                    async with db.async_session() as session:
                        stmt = select(TeamDB).where(
                            TeamDB.team_eesl_id.in_(list(team_eesl_ids))
                        )
                        results = await session.execute(stmt)
                        teams_by_eesl_id = {
                            team.team_eesl_id: team for team in results.scalars().all()
                        }

                    for m in matches_list:
                        try:
                            self.logger.debug(f"Parsed match: {m}")
                            team_a = teams_by_eesl_id.get(m["team_a_eesl_id"])
                            if team_a:
                                self.logger.debug(f"team_a: {team_a}")
                            else:
                                self.logger.error("Home team(a) not found")
                                raise
                            team_b = teams_by_eesl_id.get(m["team_b_eesl_id"])
                            if team_b:
                                self.logger.debug(f"team_a: {team_b}")
                            else:
                                self.logger.error("Away team(b) not found")
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
                            await playclock_service.create(playclock_schema)

                            gameclock_schema = GameClockSchemaCreate(
                                match_id=created_match.id
                            )
                            await gameclock_service.create(gameclock_schema)

                            existing_match_data = await asyncio.gather(
                                match_data_service.get_match_data_by_match_id(
                                    created_match.id
                                )
                            )
                            existing_match_data = existing_match_data[0]

                            if existing_match_data is None:
                                match_data_schema_create = MatchDataSchemaCreate(
                                    match_id=created_match.id,
                                    score_team_a=m["score_team_a"],
                                    score_team_b=m["score_team_b"],
                                )
                                match_data = await match_data_service.create(
                                    match_data_schema_create
                                )
                            else:
                                match_data_schema_update = MatchDataSchemaUpdate(
                                    match_id=created_match.id,
                                    score_team_a=m["score_team_a"],
                                    score_team_b=m["score_team_b"],
                                )
                                match_data = await match_data_service.update(
                                    existing_match_data.id, match_data_schema_update
                                )

                            existing_scoreboard = await asyncio.gather(
                                scoreboard_service.get_scoreboard_by_match_id(
                                    created_match.id
                                )
                            )
                            existing_scoreboard = existing_scoreboard[0]

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
                                existing_data = existing_scoreboard.__dict__
                                default_data = ScoreboardSchemaCreate().model_dump()

                                for key, value in default_data.items():
                                    if (
                                        key not in existing_data
                                        or existing_data[key] is None
                                    ):
                                        existing_data[key] = value

                                scoreboard_schema = ScoreboardSchemaUpdate(
                                    **existing_data
                                )

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
                    self.logger.warning("Matches list is empty")
                    return []
            except Exception as ex:
                self.logger.error(
                    f"Error on parse and create matches from tournament: {ex}",
                    exc_info=True,
                )

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
