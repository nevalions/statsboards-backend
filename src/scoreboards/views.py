import json

import asyncio
import os

from typing import List

from fastapi import HTTPException, Depends, status
from fastapi.templating import Jinja2Templates

from src.core import BaseRouter, db
from src.core.config import static_path_scoreboard, scoreboard_template_path
from .db_services import ScoreboardServiceDB
from .shemas import ScoreboardSchema, ScoreboardSchemaCreate, ScoreboardSchemaUpdate

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse

scoreboard_templates = Jinja2Templates(directory=scoreboard_template_path)

# Create an asyncio Queue
update_queue = asyncio.Queue()

teams_data = {
    "team_a": {
        "title": "Team Home",
        "team_logo_url": "static/logos/Griffins.jpg",
    },
    "team_b": {
        "title": "Team Away",
        "team_logo_url": "static/logos/Patriots.png",
    },
}

game_data = {
    "match_date": "now",
    "game_status": "in-progress",
    "field_length": 92,
    "score_team_a": 0,
    "score_team_b": 0,
    "timeout_team_a": "●●●",
    "timeout_team_b": "●●●",
    "qtr": "1st",
    "gameclock_status": "stopped",
    "gameclock": 720,
    "game_clock_task": None,
    "paused_time": None,
    "playclock": 40,
    "playclock_status": "stopped",
    "ball_on": 20,
    "down": "1st",
    "distance": "10",
}

scoreboard_data = {
    "is_qtr": True,
    "is_time": True,
    "is_playclock": True,
    "is_downdistance": True,
    "team_a_color": "#c01c28",
    "team_b_color": "#1c71d8",
}


# Team backend
class ScoreboardRouter(
    BaseRouter[
        ScoreboardSchema,
        ScoreboardSchemaCreate,
        ScoreboardSchemaUpdate,
    ]
):
    def __init__(self, service: ScoreboardServiceDB):
        super().__init__("/api/scoreboards", ["scoreboards"], service)

    def route(self):
        router = super().route()

        # async def event_generator():
        #     while True:
        #         # Wait for an item to be put into the queue
        #         data = await update_queue.get()
        #
        #         # Combine teams_data, game_data, and scoreboard_data
        #         # in the data sent to the client
        #         data["teams_data"] = teams_data
        #         data["game_data"] = game_data
        #         data["scoreboard_data"] = scoreboard_data
        #
        #         # Generate the data you want to send to the client
        #         yield f"data: {json.dumps(data)}\n\n"
        #
        # @router.get("/events/")
        # async def sse_endpoint(request: Request):
        #     return StreamingResponse(
        #         event_generator(),
        #         media_type="text/event-stream",
        #     )
        #
        # async def trigger_update():
        #     # Put the updated data into the queue
        #     await update_queue.put(
        #         {
        #             "teams_data": teams_data,
        #             "game_data": game_data,
        #             "scoreboard_data": scoreboard_data,
        #         }
        #     )

        @router.post(
            "/",
            response_model=ScoreboardSchema,
        )
        async def create_scoreboard(scoreboard: ScoreboardSchemaCreate):
            new_scoreboard = await self.service.create_scoreboard(scoreboard)
            return new_scoreboard.__dict__

        @router.put(
            "/{item_id}/",
            response_model=ScoreboardSchema,
        )
        async def update_scoreboard_(
            item_id: int,
            item: ScoreboardSchemaUpdate,
        ):
            update_ = await self.service.update_scoreboard(
                item_id,
                item,
            )
            if update_:
                return update_

            raise HTTPException(
                status_code=404,
                detail=f"Scoreboard id:{item_id} not found",
            )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_scoreboard_by_id(
            item_id: int,
            item=Depends(update_scoreboard_),
        ):
            if item:
                return {
                    "content": item.__dict__,
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"Scoreboard id:{item_id} not found",
            )

        # def create_directories():
        #     if not os.path.exists(static_path):
        #         os.makedirs(static_path)
        #     logos_path = os.path.join(static_path, "logos")
        #     if not os.path.exists(logos_path):
        #         os.makedirs(logos_path)

        # async def decrement_playclock(data):
        #     if data["time"]["playclock"] > 0:
        #         data["time"]["playclock"] -= 1
        #     else:
        #         # Stop the game clock when it reaches 0
        #         data["time"]["playclock-status"] = "stopped"
        #         await asyncio.sleep(3)
        #         data["time"]["playclock"] = None
        #         await stop_playclock()
        #         print("Play clock reached 0. Stopping game clock.")
        #
        # async def run_play_clock(data):
        #     while data["time"]["playclock-status"] == "running":
        #         await asyncio.sleep(1)
        #         await decrement_playclock(data)
        #         # await update_queue.put({'teams': teams_data, 'game': data})
        #         await trigger_update()
        #     await trigger_update()
        #
        # async def decrement_gameclock(data):
        #     if (
        #             data["time"]["gameclock-status"] == "running"
        #             and data["time"]["gameclock"] > 0
        #     ):
        #         data["time"]["gameclock"] -= 1
        #     elif data["time"]["gameclock-status"] == "running":
        #         # Stop the game clock when it reaches 0
        #         data["time"]["gameclock-status"] = "stopped"
        #         print("Game clock reached 0. Stopping game clock.")
        #
        # async def run_game_clock(data):
        #     while data["time"]["gameclock-status"] == "running":
        #         await asyncio.sleep(1)
        #         await decrement_gameclock(data)
        #         # await update_queue.put({'teams': teams_data, 'game': data})
        #         await trigger_update()
        #     await trigger_update()
        #
        # @router.post(
        #     "/api/start_gameclock",
        #     response_class=JSONResponse,
        # )
        # async def start_gameclock(data: dict):
        #     global game_data
        #     global game_clock_task_info
        #
        #     if game_data["time"]["gameclock-status"] == "stopped":
        #         # If the game clock is not already running or paused, start it
        #         initial_time = int(data.get("initial_time", 720))
        #         game_data["time"]["gameclock"] = initial_time
        #         game_data["time"]["gameclock-status"] = "running"
        #
        #         # Create a new task and store it in game_data
        #         game_clock_task_info = asyncio.create_task(run_game_clock(game_data))
        #
        #         return {
        #             "success": True,
        #             "message": f"Game clock started with initial time {initial_time} seconds",
        #         }
        #     elif game_data["time"]["gameclock-status"] == "paused":
        #         # If the game clock is paused, resume it
        #         game_data["time"]["gameclock-status"] = "running"
        #
        #         # Create a new task and store it in game_data
        #         game_clock_task_info = asyncio.create_task(run_game_clock(game_data))
        #
        #         return {"success": True, "message": "Game clock resumed."}
        #     else:
        #         # If the game clock is already running, return a message
        #         return {"success": False, "message": "Game clock is already running."}
        #
        # @router.post(
        #     "/api/pause_gametimer",
        #     response_class=JSONResponse,
        # )
        # async def pause_gametimer():
        #     global game_data
        #
        #     if game_data["time"]["gameclock-status"] == "running":
        #         # If the game clock is running, pause it
        #         game_data["time"]["gameclock-status"] = "paused"
        #
        #         # Cancel the run_game_clock task
        #         if game_clock_task_info:
        #             game_clock_task_info.cancel()
        #
        #         await trigger_update()
        #         return {"success": True, "message": "Game clock paused."}
        #     else:
        #         # If the game clock is not running, return a message
        #         return {"success": False, "message": "Game clock is not running."}
        #
        # @router.get(
        #     "/api/stop_gameclock",
        #     response_class=JSONResponse,
        # )
        # async def stop_gameclock():
        #     global game_data
        #
        #     if (
        #             game_data["time"]["gameclock-status"] in ("running", "paused")
        #             and game_clock_task_info
        #     ):
        #         # If the game clock is running or paused, stop it
        #         game_data["time"]["gameclock"] = 720
        #         game_data["time"]["gameclock-status"] = "stopped"
        #         game_clock_task_info.cancel()
        #         await trigger_update()
        #         # await update_queue.put({'teams': teams_data, 'game': game_data})
        #         return {"success": True, "message": "Game clock stopped."}
        #     else:
        #         # If the game clock is already stopped, return a message
        #         return {"success": False, "message": "Game clock is already stopped."}
        #
        # @router.post("/api/save_new_clock_params")
        # async def save_new_clock_params(data: dict):
        #     global game_data
        #
        #     try:
        #         minutes = int(data.get("minutes", 0))
        #         seconds = int(data.get("seconds", 0))
        #
        #         # Validate the input
        #         # (you can add more validation logic based on your requirements)
        #         if not (0 <= minutes <= 59) or not (0 <= seconds <= 59):
        #             raise HTTPException(status_code=400, detail="Invalid input values")
        #
        #         # Calculate the total time in seconds
        #         total_seconds = minutes * 60 + seconds
        #
        #         # Check if the game clock is currently running
        #         if game_data["time"]["gameclock-status"] == "running":
        #             # If running, update the remaining time on the clock
        #             remaining_time = game_data["time"]["gameclock"] - (
        #                     game_data["time"]["gameclock"] - total_seconds
        #             )
        #             game_data["time"]["gameclock"] = remaining_time
        #             await trigger_update()
        #             return {
        #                 "success": True,
        #                 "message": "Game clock parameters updated successfully.",
        #             }
        #         else:
        #             # If not running, update the initial time
        #             game_data["time"]["gameclock"] = total_seconds
        #
        #         await trigger_update()
        #         return {
        #             "success": True,
        #             "message": "Clock parameters saved successfully.",
        #         }
        #
        #     except ValueError:
        #         raise HTTPException(
        #             status_code=400,
        #             detail="Invalid input values",
        #         )
        #
        # @router.get(
        #     "/api/get_gameclock",
        #     response_class=JSONResponse,
        # )
        # async def get_gameclock():
        #     global game_data
        #     gameclock = game_data["time"]["gameclock"]
        #     print(gameclock)
        #     return {"time": {"gameclock": gameclock}}
        #
        # @router.post(
        #     "/api/start_playclock",
        #     response_class=JSONResponse,
        # )
        # async def start_playclock(data: dict):
        #     global game_data
        #     global play_clock_task_info
        #
        #     if game_data["time"]["playclock-status"] == "stopped":
        #         initial_time = int(data.get("initial_time", 40))
        #         game_data["time"]["playclock"] = initial_time
        #         game_data["time"]["playclock-status"] = "running"
        #
        #         play_clock_task_info = asyncio.create_task(run_play_clock(game_data))
        #
        #         return {
        #             "success": True,
        #             "message": f"Playclock started with initial time {initial_time} seconds",
        #         }
        #
        #     # Check if the 'decrement_playclock' task is already running,
        #     # and set the flag accordingly
        #     else:
        #         initial_time = int(data.get("initial_time", 40))
        #         # If play clock is already running, stop and restart it
        #         await stop_playclock()
        #         game_data["time"]["playclock"] = initial_time
        #         game_data["time"]["playclock-status"] = "running"
        #         play_clock_task_info = asyncio.create_task(run_play_clock(game_data))
        #
        #         return {
        #             "success": True,
        #             "message": f"Play clock restarted with initial time {initial_time} seconds",
        #         }
        #
        # @router.get("/api/stop_playclock", response_class=JSONResponse)
        # async def stop_playclock():
        #     global game_data
        #
        #     # Cancel the 'decrement_playclock' task if running
        #     if (
        #             game_data["time"]["playclock-status"] == "running"
        #             and play_clock_task_info
        #     ):
        #         game_data["time"]["playclock-status"] = "stopped"
        #         play_clock_task_info.cancel()
        #         game_data["time"]["playclock"] = None
        #         await trigger_update()
        #         return {
        #             "success": True,
        #             "message": "Play clock stopped.",
        #         }
        #     else:
        #         return {
        #             "success": False,
        #             "message": "Play clock is already stopped.",
        #         }
        #
        # @router.get(
        #     "/api/get_playclock",
        #     response_class=JSONResponse,
        # )
        # async def get_playclock():
        #     global game_data
        #     playclock = game_data["time"]["playclock"]
        #     print(playclock)
        #     return {"time": {"playclock": playclock}}
        #

        #

        # @router.post(
        #     "/api/change_logo/{team}",
        #     response_class=JSONResponse,
        # )
        # async def change_logo(team: str, logo: UploadFile = File(...)):
        #     create_directories()
        #
        #     if logo:
        #         file_ext = logo.filename.split(".")[-1]
        #
        #         # Ensure the 'static' folder exists
        #         if not os.path.exists(static_path):
        #             os.makedirs("static")
        #
        #         # Save the uploaded logo file
        #         logo_path = os.path.join(
        #             static_path,
        #             f'logos/{teams_data[team]["name"]}_new.{file_ext}',
        #         )
        #         print(logo_path)
        #         with open(logo_path, "wb") as f:
        #             f.write(logo.file.read())
        #
        #         # Update the team's logo path in the teams_data dictionary
        #         teams_data[team][
        #             "logo"
        #         ] = f'static/logos/{teams_data[team]["name"]}_new.{file_ext}'
        #
        #         await trigger_update()
        #         return {"success": True}
        #     else:
        #         return {
        #             "success": False,
        #             "error": "No logo file provided",
        #         }

        return router


api_scoreboards_router = ScoreboardRouter(ScoreboardServiceDB(db)).route()
