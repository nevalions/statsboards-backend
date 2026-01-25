import time
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    status,
)
from fastapi.responses import JSONResponse

from src.auth.dependencies import require_roles
from src.core import BaseRouter, db
from src.core.models import GameClockDB

from ..logging_config import get_logger
from .db_services import GameClockServiceDB
from .schemas import GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate


class GameClockAPIRouter(BaseRouter[GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate]):
    def __init__(self, service: GameClockServiceDB):
        super().__init__(
            "/api/gameclock",
            ["gameclock"],
            service,
        )
        self.logger = get_logger("backend_logger_GameClockAPIRouter", self)
        self.logger.debug("Initialized GameClockAPIRouter")

    def create_response_with_server_time(self, item, message: str):
        response_data = GameClockSchema.model_validate(item).model_dump()
        response_data["server_time_ms"] = int(time.time() * 1000)
        return {
            "content": response_data,
            "status_code": status.HTTP_200_OK,
            "success": True,
            "message": message,
        }

    def create_error_response(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        return {
            "content": None,
            "status_code": status_code,
            "success": False,
            "message": message,
        }

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
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creating gameclock: {str(ex)}",
                ) from ex

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
                if gameclock_update is None:
                    raise HTTPException(status_code=404, detail=f"Gameclock {item_id} not found")
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
                    detail="Error updating gameclock with data",
                ) from ex

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_gameclock_by_id(
            item_id: int,
            item=Depends(update_gameclock_),
        ):
            self.logger.debug("Update gameclock endpoint by ID")
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
        async def start_gameclock_endpoint(background_tasks: BackgroundTasks, gameclock_id: int):
            self.logger.debug(f"Start gameclock endpoint with id: {gameclock_id}")
            try:
                gameclock = await self.service.get_by_id(gameclock_id)
                present_gameclock_status = gameclock.gameclock_status

                # If the gameclock was not running, then start it
                if present_gameclock_status != "running":
                    started_at_ms = int(time.time() * 1000)

                    # Update the gameclock status to running
                    updated = await self.service.update(
                        gameclock_id,
                        GameClockSchemaUpdate(
                            gameclock_status="running",
                            gameclock_time_remaining=gameclock.gameclock,
                            started_at_ms=started_at_ms,
                        ),
                    )

                    # Ensure state machine exists
                    state_machine = self.service.clock_manager.get_clock_state_machine(gameclock_id)
                    if not state_machine:
                        self.logger.debug(
                            f"State machine not found, creating new one for gameclock {gameclock_id}"
                        )
                        await self.service.clock_manager.start_clock(
                            gameclock_id, gameclock.gameclock
                        )
                        state_machine = self.service.clock_manager.get_clock_state_machine(
                            gameclock_id
                        )

                    # Update state machine
                    if state_machine:
                        state_machine.started_at_ms = started_at_ms
                        state_machine.status = "running"

                    if hasattr(self.service, "cache_service") and self.service.cache_service:
                        self.service.cache_service.invalidate_gameclock(gameclock_id)

                    return self.create_response_with_server_time(
                        updated,
                        f"Game clock ID:{gameclock_id} {updated.gameclock_status}",
                    )
                else:
                    return self.create_response_with_server_time(
                        gameclock,
                        f"Game clock ID:{gameclock_id} already {present_gameclock_status}",
                    )
            except Exception as ex:
                self.logger.error(
                    f"Error on starting gameclock with id:{gameclock_id} {ex}",
                    exc_info=True,
                )
                return self.create_error_response(
                    f"Error starting gameclock: {str(ex)}",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
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
                state_machine = self.service.clock_manager.get_clock_state_machine(item_id)
                current_value = None

                if state_machine:
                    self.logger.debug(f"Found state machine for gameclock {item_id}")
                    current_value = state_machine.get_current_value()
                    self.logger.debug(f"Current value from state machine: {current_value}")
                    self.logger.debug(f"Current status from state machine: {state_machine.status}")
                    self.logger.debug(f"State machine value after pause: {state_machine.value}")
                else:
                    self.logger.warning(
                        f"No state machine found for gameclock {item_id}, getting from DB"
                    )

                if current_value is None:
                    gameclock_db = await self.service.get_by_id(item_id)
                    if gameclock_db:
                        current_value = gameclock_db.gameclock
                        self.logger.debug(f"Current value from DB: {current_value}")

                await self.service.stop_gameclock(item_id)

                update_data = GameClockSchemaUpdate(
                    gameclock_status=item_status,
                    gameclock=current_value,
                    gameclock_time_remaining=current_value,
                    started_at_ms=None,
                )
                self.logger.debug(
                    f"Updating gameclock {item_id} with status={item_status}, value={current_value}"
                )

                updated_ = await self.service.update(
                    item_id,
                    update_data,
                )
                if updated_:
                    if hasattr(self.service, "cache_service") and self.service.cache_service:
                        self.service.cache_service.invalidate_gameclock(item_id)
                    return self.create_response_with_server_time(
                        updated_,
                        f"Game clock ID:{item_id} {item_status}",
                    )
                else:
                    return self.create_error_response(
                        f"Game clock ID:{item_id} not found",
                        status.HTTP_404_NOT_FOUND,
                    )
            except Exception as ex:
                self.logger.error(
                    f"Error on pausing gameclock with id:{item_id} {ex}", exc_info=True
                )
                return self.create_error_response(
                    f"Error pausing gameclock: {str(ex)}",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
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

                if not updated:
                    return self.create_error_response(
                        f"Game clock ID:{item_id} not found",
                        status.HTTP_404_NOT_FOUND,
                    )

                if hasattr(self.service, "cache_service") and self.service.cache_service:
                    self.service.cache_service.invalidate_gameclock(item_id)

                return self.create_response(
                    updated,
                    f"Game clock {item_status}",
                )
            except Exception as ex:
                self.logger.error(
                    f"Error on resetting gameclock with id:{item_id} {ex}",
                    exc_info=True,
                )
                return self.create_error_response(
                    f"Error resetting gameclock: {str(ex)}",
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        @router.delete(
            "/id/{model_id}",
            summary="Delete gameclock",
            description="Delete a gameclock by ID. Requires admin role.",
            responses={
                200: {"description": "Gameclock deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Gameclock not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_gameclock_endpoint(
            model_id: int,
            _: Annotated[GameClockDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete gameclock endpoint id:{model_id}")
            await self.service.delete(model_id)
            return {"detail": f"Gameclock {model_id} deleted successfully"}

        return router


api_gameclock_router = GameClockAPIRouter(GameClockServiceDB(db)).route()
