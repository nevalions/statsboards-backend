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
from ..logging_config import get_logger, setup_logging

setup_logging()


class GameClockAPIRouter(
    BaseRouter[GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate]
):
    def __init__(self, service: GameClockServiceDB):
        super().__init__(
            "/api/gameclock",
            ["gameclock"],
            service,
        )
        self.logger = get_logger("backend_logger_GameClockAPIRouter", self)
        self.logger.debug(f"Initialized GameClockAPIRouter")

    def route(self):
        router = super().route()

        # Gameclock backend
        @router.post(
            "/",
            response_model=GameClockSchema,
        )
        async def create_gameclock_endpoint(gameclock_data: GameClockSchemaCreate):
            self.logger.debug(f"Create gameclock endpoint got data: {gameclock_data}")
            try:
                new_gameclock = await self.service.create(gameclock_data)
                return GameClockSchema.model_validate(new_gameclock)
            except Exception as ex:
                self.logger.error(
                    f"Error creating gameclock with data: {gameclock_data} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/{item_id}/",
            response_model=GameClockSchema,
        )
        async def update_gameclock_(
            item_id: int,
            item: GameClockSchemaUpdate,
        ):
            self.logger.debug(f"Update gameclock endpoint id:{item_id} data: {item}")
            try:
                gameclock_update = await self.service.update(
                    item_id,
                    item,
                )
                return gameclock_update
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error updating gameclock with data: {item} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"Error updating gameclock with data",
                )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_gameclock_by_id(
            item_id: int,
            item=Depends(update_gameclock_),
        ):
            self.logger.debug(f"Update gameclock endpoint by ID")
            if item:
                return {
                    "content": GameClockSchema.model_validate(item).model_dump(),
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
            self.logger.debug(f"Start gameclock endpoint with id: {gameclock_id}")
            try:
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
                    if not self.service.disable_background_tasks:
                        self.logger.debug(
                            f"Start gameclock background task, loop decrement"
                        )
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
            except Exception as ex:
                self.logger.error(
                    f"Error on starting gameclock with id:{gameclock_id} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/id/{item_id}/paused/",
            response_class=JSONResponse,
        )
        async def pause_gameclock_endpoint(
            item_id: int,
        ):
            self.logger.debug(f"Pausing gameclock endpoint with id: {item_id}")
            item_status = "paused"

            try:
                updated_ = await self.service.update(
                    item_id,
                    GameClockSchemaUpdate(gameclock_status=item_status),
                )
                if updated_:
                    return self.create_response(
                        updated_,
                        f"Game clock ID:{item_id} {item_status}",
                    )
            except Exception as ex:
                self.logger.error(
                    f"Error on pausing gameclock with id:{item_id} {ex}", exc_info=True
                )

        @router.put(
            "/id/{item_id}/{item_status}/{sec}/",
            response_class=JSONResponse,
        )
        async def reset_gameclock_endpoint(
            item_id: int,
            item_status: str = Path(
                ...,
                examples=["stopped"],
            ),
            sec: int = Path(
                ...,
                description="Seconds",
                examples=[720],
            ),
        ):
            self.logger.debug(f"Resetting gameclock endpoint with id: {item_id}")
            try:
                updated = await self.service.update(
                    item_id,
                    GameClockSchemaUpdate(gameclock=sec, gameclock_status=item_status),
                )

                return self.create_response(
                    updated,
                    f"Game clock {item_status}",
                )
            except Exception as ex:
                self.logger.error(
                    f"Error on resetting gameclock with id:{item_id} {ex}",
                    exc_info=True,
                )

        return router


api_gameclock_router = GameClockAPIRouter(GameClockServiceDB(db)).route()
