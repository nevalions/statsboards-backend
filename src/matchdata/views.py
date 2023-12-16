from typing import Optional, Any

from fastapi import HTTPException, Depends, Path, Query, status
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import MatchDataServiceDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate, MatchDataSchema

game_clock_task_info = None
play_clock_task_info = None


class MatchDataRouter(
    BaseRouter[
        MatchDataSchema,
        MatchDataSchemaCreate,
        MatchDataSchemaUpdate,
    ]
):
    def __init__(self, service: MatchDataServiceDB):
        super().__init__(
            "/api/matchdata",
            ["matchdata"],
            service,
        )

    def route(self):
        router = super().route()

        # Match data backend
        @router.post(
            "/",
            response_model=MatchDataSchema,
        )
        async def create_match_data(match_data: MatchDataSchemaCreate):
            new_match_data = await self.service.create_match_data(match_data)
            return new_match_data.__dict__

        @router.put(
            "/{item_id}/",
            response_model=MatchDataSchema,
        )
        async def update_match_data_(
            item_id: int,
            match: MatchDataSchemaUpdate,
        ):
            match_data_update = await self.service.update_match_data(
                item_id,
                match,
            )

            if match_data_update is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match data " f"id({item_id}) " f"not found",
                )
            return match_data_update

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_matchdata_by_id(
            item_id: int,
            item=Depends(update_match_data_),
        ):
            if item:
                return {
                    "content": item.__dict__,
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_matchdata_by_id(
            item=Depends(self.service.get_by_id),
        ):
            return self.create_response(
                item,
                f"MatchData ID:{item.id}",
            )

        @router.put(
            "/id/{item_id}/gameclock/{item_status}/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            item_id: int,
            item_status: str = Path(
                ...,
                example="running",
            ),
        ):
            updated = await self.service.update(
                item_id,
                MatchDataSchemaUpdate(gameclock_status=item_status),
            )
            await self.service.decrement_gameclock(item_id)
            return self.create_response(
                updated,
                f"Game clock {item_status}",
            )

        @router.put(
            "/id/{item_id}/gameclock/{item_status}/{sec}/",
            response_class=JSONResponse,
        )
        async def reset_gameclock_endpoint(
            item_id: int,
            item_status: str = Path(
                ...,
                example="stopped",
            ),
            sec: int = Path(
                ...,
                description="Seconds",
                example=720,
            ),
        ):
            updated = await self.service.update(
                item_id,
                MatchDataSchemaUpdate(
                    gameclock=sec,
                    gameclock_status=item_status,
                ),
            )
            return self.create_response(
                updated,
                f"Game clock {item_status}",
            )

        # await self.service.reset_gameclock(item_id)
        # return {"message": "Game clock reset"}

        # @router.put("/start_gameclock/{item_id}")
        # async def decrement_gameclock_endpoint(item_id: int):
        #     await self.service.start_gameclock(item_id)
        #     started_gameclock = await self.service.decrement_gameclock(item_id)
        #     return {"updated_gameclock": started_gameclock}

        # if game_data.gameclock - status == "stopped" | "string" | None:
        #     # If the game clock is not already running or paused, start it
        #     game_data["match_data"]["gameclock-status"] = "running"
        #
        #     # Create a new task and store it in game_data
        #     game_clock_task_info = asyncio.create_task(run_game_clock(game_data))
        #
        #     return {
        #         "success": True,
        #         "message": f"Game clock started with initial time "
        #                    f"{game_data['match_data']['gameclock']} seconds",
        #     }
        # elif game_data["match_data"]["gameclock-status"] == "paused":
        #     # If the game clock is paused, resume it
        #     game_data["match_data"]["gameclock-status"] = "running"
        #
        #     # Create a new task and store it in game_data
        #     game_clock_task_info = asyncio.create_task(run_game_clock(game_data))
        #
        #     return {"success": True, "message": "Game clock resumed."}
        # else:
        #     # If the game clock is already running, return a message
        #     return {"success": False, "message": "Game clock is already running."}

        # async def decrement_gameclock(match_data):
        #     if match_data.gameclock_status == "running" and match_data.gameclock > 0:
        #         new_gameclock = match_data.gameclock - 1
        #         print(match_data, new_gameclock)
        #         await self.service.update_match_data_gameclock(
        #             match_data.id,
        #             new_gameclock,
        #         )
        #
        #     elif match_data.gameclock_status == "running":
        #         # Stop the game clock when it reaches 0
        #         match_data.gameclock_status = "stopped"
        #         print("Game clock reached 0. Stopping game clock.")

        # async def run_game_clock(match_data):
        #     while match_data.gameclock_status == "running":
        #         print(match_data.gameclock_status, match_data.gameclock)
        #         await asyncio.sleep(1)
        #         await decrement_gameclock(match_data)

        return router

        # await update_queue.put({'teams': teams_data, 'game': data})

    #     await trigger_update()
    # await trigger_update()


api_matchdata_router = MatchDataRouter(MatchDataServiceDB(db)).route()
