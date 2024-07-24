from fastapi import (
    HTTPException,
    Depends,
    Path,
    status,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import GameClockServiceDB
from .schemas import GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate


class GameClockRouter(
    BaseRouter[GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate]
):
    def __init__(self, service: GameClockServiceDB):
        super().__init__(
            "/api/gameclock",
            ["gameclock"],
            service,
        )

    def route(self):
        router = super().route()

        # Gameclock backend
        @router.post(
            "/",
            response_model=GameClockSchema,
        )
        async def create_gameclock_endpoint(gameclock: GameClockSchemaCreate):
            new_playclock = await self.service.create_gameclock(gameclock)
            return new_playclock.__dict__

        @router.put(
            "/{item_id}/",
            response_model=GameClockSchema,
        )
        async def update_gameclock_(
            item_id: int,
            gameclock: GameClockSchemaUpdate,
        ):
            gameclock_update = await self.service.update_gameclock(
                item_id,
                gameclock,
            )

            if gameclock_update is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Gameclock " f"id({item_id}) " f"not found",
                )
            return gameclock_update

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_gameclock_by_id(
            item_id: int,
            item=Depends(update_gameclock_),
        ):
            if item:
                return {
                    "content": item.__dict__,
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"Gameclock id:{item_id} not found",
            )

        @router.put("/id/{gameclock_id}/running/", response_class=JSONResponse)
        async def start_gameclock_endpoint(
            background_tasks: BackgroundTasks, gameclock_id: int
        ):
            gameclock = await self.service.get_by_id(gameclock_id)
            present_gameclock_status = gameclock.gameclock_status

            # If the gameclock was not running, then start it
            if present_gameclock_status != "running":
                # Update the gameclock status to running
                updated = await self.service.update(
                    gameclock_id,
                    GameClockSchemaUpdate(
                        gameclock_status="running",
                        gameclock_time_remaining=gameclock.gameclock,
                    ),
                )

                # Start background task for decrementing the game clock
                background_tasks.add_task(
                    self.service.loop_decrement_gameclock, gameclock_id
                )

                return self.create_response(
                    updated,
                    f"Game clock ID:{gameclock_id} {updated.gameclock_status}",
                )
            else:
                return self.create_response(
                    gameclock,
                    f"Game clock ID:{gameclock_id} already {present_gameclock_status}",
                )

        @router.put(
            "/id/{item_id}/paused/",
            response_class=JSONResponse,
        )
        async def pause_gameclock_endpoint(
            item_id: int,
        ):
            item_status = "paused"

            updated_ = await self.service.update(
                item_id,
                GameClockSchemaUpdate(gameclock_status=item_status),
            )
            print("updated updated")
            if updated_:
                return self.create_response(
                    updated_,
                    f"Game clock ID:{item_id} {item_status}",
                )

        @router.put(
            "/id/{item_id}/{item_status}/{sec}/",
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
                GameClockSchemaUpdate(gameclock=sec, gameclock_status=item_status),
            )

            return self.create_response(
                updated,
                f"Game clock {item_status}",
            )

        return router


api_gameclock_router = GameClockRouter(GameClockServiceDB(db)).route()
