import asyncio
from typing import List

from fastapi import HTTPException, Request, Depends, status, WebSocket
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.websockets import WebSocketDisconnect

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
from ..matchdata.schemas import MatchDataSchemaCreate
from ..scoreboards.shemas import ScoreboardSchemaCreate


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
            match_db_service = MatchDataServiceDB(db)
            scoreboard_db_service = ScoreboardServiceDB(db)

            # Create all
            new_match = await self.service.create_or_update_match(data)

            default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
            default_scoreboard = ScoreboardSchemaCreate(match_id=new_match.id)
            #
            # {
            #     "field_length": 92,
            #     "game_status": "in-progress",
            #     "score_team_a": 0,
            #     "score_team_b": 0,
            #     "timeout_team_a": "●●●",
            #     "timeout_team_b": "●●●",
            #     "qtr": "1st",
            #     "gameclock": 720,
            #     "gameclock_status": "stopped",
            #     "playclock": 0,
            #     "playclock_status": "stopped",
            #     "ball_on": 20,
            #     "down": "1st",
            #     "distance": "10",
            #     "match_id": 0
            # }

            new_match_data = await match_db_service.create_match_data(default_match_data)
            teams_data = await self.service.get_teams_by_match(new_match_data.match_id)
            new_scoreboard = await scoreboard_db_service.create_scoreboard(
                default_scoreboard
            )

            # Return the created objects
            return {
                "status_code": status.HTTP_200_OK,
                "match": new_match,
                "match_data": new_match_data,
                "teams_data": teams_data,
                "scoreboard": new_scoreboard,
            }

        @router.put(
            "/",
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
                request: Request,
                match_id: int,
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
        async def full_match_data_endpoint(
                match_id: int,
                # match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
                # match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            from src.helpers.fetch_helpers import fetch_match_data

            return await fetch_match_data(match_id)
            # match = await self.service.get_by_id(match_id)
            #
            # return {
            #     "status_code": status.HTTP_200_OK,
            #     "teams_data": match_teams_data,
            #     "match": match,
            #     "match_data": match_data.__dict__,
            # }

        @router.get(
            "/id/{match_id}/scoreboard/full_data/scoreboard_settings/",
            response_class=JSONResponse,
        )
        async def full_match_data_with_scoreboard_endpoint(
                match_id: int,
                # match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
                # match_data=Depends(get_match_data_by_match_id_endpoint),
                # scoreboard_data=Depends(get_match_scoreboard_by_match_id_endpoint),
        ):
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            return await fetch_with_scoreboard_data(match_id)
            # match = await self.service.get_by_id(match_id)
            #
            # return {
            #     "status_code": status.HTTP_200_OK,
            #     "teams_data": match_teams_data,
            #     "match": match,
            #     "match_data": match_data.__dict__,
            #     "scoreboard_data": scoreboard_data.__dict__,
            # }

        # async def full_match_data_endpoint(
        #     match_id: int,
        # ):
        #     from src.helpers.fetch_helpers import fetch_with_scoreboard_data
        #
        #     return await fetch_with_scoreboard_data(match_id)
        @router.websocket("/ws/id/{match_id}")
        async def match_websocket_endpoint(websocket: WebSocket, match_id: int):
            await websocket.accept()

            full_route = f"ws://[YOUR_HOST]:[YOUR_PORT]{websocket.url.path}"
            print("Full route of the websocket:", full_route)

            while True:
                try:
                    from src.helpers.fetch_helpers import fetch_with_scoreboard_data
                    full_match_data = await fetch_with_scoreboard_data(match_id)

                    # Send the updated data to the client
                    await websocket.send_json(full_match_data)

                    # Sleep for some time (say 1 sec) before fetching the updated data
                    await asyncio.sleep(0.5)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    # Close the connection if an error occurs and send the reason to the client
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break

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
