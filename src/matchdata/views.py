import asyncio
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
)
from fastapi.responses import JSONResponse

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import MatchDataService
from src.core.enums import GameStatus
from src.core.models import MatchDataDB

from ..logging_config import get_logger
from .schemas import MatchDataSchema, MatchDataSchemaCreate, MatchDataSchemaUpdate


class MatchDataAPIRouter(
    BaseRouter[
        MatchDataSchema,
        MatchDataSchemaCreate,
        MatchDataSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/matchdata",
            ["matchdata"],
            None,
        )
        self.logger = get_logger("MatchDataAPIRouter", self)
        self.logger.debug("Initialized MatchDataAPIRouter")

    def route(self):
        router = super().route()

        # Match data backend
        @router.post(
            "/",
            response_model=MatchDataSchema,
        )
        async def create_match_data(
            match_data_service: MatchDataService, match_data: MatchDataSchemaCreate
        ):
            self.logger.debug(f"Create matchdata endpoint got data: {match_data}")
            try:
                new_match_data = await match_data_service.create(match_data)
                return MatchDataSchema.model_validate(new_match_data)
            except Exception as ex:
                self.logger.error(
                    f"Error creating matchdata with data: {match_data} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/{item_id}/",
            response_model=MatchDataSchema,
        )
        async def update_match_data_(
            match_data_service: MatchDataService,
            item_id: int,
            match_data: MatchDataSchemaUpdate,
        ):
            self.logger.debug(f"Update matchdata endpoint id:{item_id} data: {match_data}")
            try:
                match_data_update = await match_data_service.update(
                    item_id,
                    match_data,
                )
                if match_data_update is None:
                    raise HTTPException(status_code=404, detail=f"MatchData {item_id} not found")
                return match_data_update
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error updating matchdata with data: {match_data} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail="Error updating matchdata with data",
                ) from ex

        @router.put(
            "/id/{item_id}/",
            response_model=MatchDataSchema,
        )
        async def update_matchdata_by_id(
            item_id: int,
            item=Depends(update_match_data_),
        ):
            self.logger.debug("Update matchdata by ID")
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"MatchData id:{item_id} not found",
                )
            return MatchDataSchema.model_validate(item)

        @router.get(
            "/id/{item_id}/",
            response_model=MatchDataSchema,
        )
        async def get_matchdata_by_id(
            match_data_service: MatchDataService,
            item_id: int,
        ):
            self.logger.debug("Get matchdata by id endpoint")
            item = await match_data_service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"MatchData id:{item_id} not found",
                )
            return MatchDataSchema.model_validate(item)

        @router.put(
            "/id/{match_data_id}/gameclock/running/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            match_data_service: MatchDataService,
            background_tasks: BackgroundTasks,
            match_data_id: int,
        ):
            self.logger.debug("Start gameclock endpoint")

            try:
                start_game = "in-progress"
                self.logger.debug(f"Start gameclock with matchdata id: {match_data_id}")
                await match_data_service.update(
                    match_data_id,
                    MatchDataSchemaUpdate(
                        game_status=start_game,
                    ),
                )
            except Exception as ex:
                self.logger.error(
                    f"Error updating matchdata on gameclock with data: {match_data_id} {ex}",
                    exc_info=True,
                )
            tasks = [
                match_data_service.enable_match_data_clock_queues(
                    match_data_id,
                    "game",
                ),
            ]
            self.logger.debug(f"Enabled tasks {tasks}")

            await asyncio.gather(*tasks)

            item_status = "running"
            try:
                self.logger.debug(f"Start gameclock with matchdata id: {match_data_id}")
                match_data = await match_data_service.get_by_id(match_data_id)
                present_gameclock_status = match_data.gameclock_status
                self.logger.debug(f"Present gameclock status: {present_gameclock_status}")

                if present_gameclock_status != "running":
                    self.logger.debug("Gameclock not running")
                    updated = await match_data_service.update(
                        match_data_id,
                        MatchDataSchemaUpdate(
                            gameclock_status=item_status,
                        ),
                    )

                    self.logger.debug("Go to decrement gameclock")
                    await match_data_service.decrement_gameclock(
                        background_tasks,
                        match_data_id,
                    )

                    self.logger.debug(f"Gameclock updated {updated}")
                    return self.create_response(
                        updated,
                        f"Gameclock Match Data ID:{match_data_id} {item_status}",
                    )
                else:
                    self.logger.debug(f"Gameclock already {present_gameclock_status}")
                    return self.create_response(
                        match_data,
                        f"Gameclock Match Data ID:{match_data_id} already {present_gameclock_status}",
                    )
            except Exception as ex:
                self.logger.error(
                    f"Error on gameclock update matchdata id:{match_data_id} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/id/{item_id}/gameclock/paused/",
            response_class=JSONResponse,
        )
        async def pause_gameclock_endpoint(
            match_data_service: MatchDataService,
            background_tasks: BackgroundTasks,
            item_id: int,
        ):
            self.logger.debug("Pause gameclock endpoint")
            item_status = "paused"
            try:
                updated_ = await match_data_service.update(
                    item_id,
                    MatchDataSchemaUpdate(gameclock_status=item_status),
                )
                if updated_:
                    self.logger.debug(f"Game clock id:{item_id} {item_status}")
                    return self.create_response(
                        updated_,
                        f"Game clock ID:{item_id} {item_status}",
                    )
            except Exception as ex:
                self.logger.error(f"Error pausing gameclock id: {item_id} {ex}", exc_info=True)

        @router.put(
            "/id/{item_id}/gameclock/{item_status}/{sec}/",
            response_class=JSONResponse,
        )
        async def reset_gameclock_endpoint(
            match_data_service: MatchDataService,
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
            try:
                self.logger.debug("Reset gameclock endpoint")
                await match_data_service.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        gameclock=sec,
                        gameclock_status=item_status,
                        game_status=GameStatus.STOPPING,
                    ),
                )
            except Exception as ex:
                self.logger.error(f"Error updating gameclock id: {item_id} {ex}", exc_info=True)

            # await match_data_service.trigger_update_match_clock(item_id, "game")

            try:
                updated = await match_data_service.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        gameclock=sec,
                        gameclock_status=item_status,
                        game_status=GameStatus.STOPPED,
                    ),
                )

                # await match_data_service.trigger_update_match_clock(item_id, "game")
                self.logger.debug(f"Game clock id:{item_id} {item_status}")
                return self.create_response(
                    updated,
                    f"Game clock {item_status}",
                )
            except Exception as ex:
                self.logger.error(f"Error while reset gameclock id: {item_id} {ex}", exc_info=True)

        @router.put(
            "/id/{item_id}/playclock/running/{sec}/",
            response_class=JSONResponse,
        )
        async def start_playclock_endpoint(
            match_data_service: MatchDataService,
            background_tasks: BackgroundTasks,
            item_id: int,
            sec: int = Path(..., description="Seconds", examples=[720]),
        ):
            self.logger.debug("Start playclock endpoint")
            item_status = "running"

            try:
                item = await match_data_service.get_by_id(item_id)
                present_playclock_status = item.playclock_status

                await match_data_service.enable_match_data_clock_queues(
                    item_id,
                    "play",
                )
                if present_playclock_status != "running":
                    self.logger.debug("Playclock not running")
                    await match_data_service.update(
                        item_id,
                        MatchDataSchemaUpdate(
                            playclock=sec,
                            playclock_status=item_status,
                        ),
                    )

                    self.logger.debug("Go to decrement playclock")
                    await match_data_service.decrement_playclock(
                        background_tasks,
                        item_id,
                    )

                    return self.create_response(
                        item,
                        f"Play clock ID:{item_id} {item_status}",
                    )
                else:
                    return self.create_response(
                        item,
                        f"Play clock ID:{item_id} already {present_playclock_status}",
                    )
            except Exception as ex:
                self.logger.error(
                    f"Error on playclock start matchdata id:{item_id} {ex}",
                    exc_info=True,
                )

        @router.put(
            "/id/{item_id}/playclock/stopped/",
            response_class=JSONResponse,
        )
        async def reset_playclock_endpoint(
            match_data_service: MatchDataService,
            item_id: int,
        ):
            item_status = "stopped"
            self.logger.debug(f"Reset playclock id{item_id} endpoint")

            await match_data_service.update(
                item_id,
                MatchDataSchemaUpdate(
                    playclock=None,
                    playclock_status="stopping",
                ),
            )

            # await match_data_service.trigger_update_match_clock(item_id, "play")

            updated = await match_data_service.update(
                item_id,
                MatchDataSchemaUpdate(
                    playclock_status="stopped",
                ),
            )

            return self.create_response(
                updated,
                f"Play clock {item_status}",
            )

        """triggers for sse process, now we use websocket"""
        # @router.get("/id/{match_data_id}/events/gamedata/")
        # async def sse_match_data_endpoint(match_data_id: int):
        #     return StreamingResponse(
        #         match_data_service.event_generator_get_match_data(match_data_id),
        #         media_type="text/event-stream",
        #     )
        #
        # @router.get("/id/{match_data_id}/events/playclock/")
        # async def sse_match_data_playclock_endpoint(match_data_id: int):
        #     return StreamingResponse(
        #         match_data_service.event_generator_get_match_clock(
        #             match_data_id,
        #             "play",
        #         ),
        #         media_type="text/event-stream",
        #     )
        #
        # @router.get("/id/{match_data_id}/events/gameclock/")
        # async def sse_match_data_gameclock_endpoint(match_data_id: int):
        #     return StreamingResponse(
        #         match_data_service.event_generator_get_match_clock(
        #             match_data_id,
        #             "game",
        #         ),
        #         media_type="text/event-stream",
        #     )

        # @router.get("/id/{match_data_id}/events/gameclock/")
        # async def sse_match_data_gameclock_endpoint(match_data_id: int):
        #
        #     await match_data_service.enable_match_data_events_queues(match_data_id)
        #
        #     return StreamingResponse(
        #         match_data_service.event_generator_get_match_data_gameclock(
        #             match_data_id
        #         ),
        #         media_type="text/event-stream",
        #     )

        # @router.get(
        #     "/queue/",
        #     response_class=JSONResponse,
        # )
        # async def queue():
        #     return await match_data_service.get_active_match_ids()

        @router.delete(
            "/id/{model_id}",
            summary="Delete matchdata",
            description="Delete matchdata by ID. Requires admin role.",
            responses={
                200: {"description": "MatchData deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "MatchData not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_matchdata_endpoint(
            match_data_service: MatchDataService,
            model_id: int,
            _: Annotated[MatchDataDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete matchdata endpoint id:{model_id}")
            await match_data_service.delete(model_id)
            return {"detail": f"MatchData {model_id} deleted successfully"}

        return router


api_matchdata_router = MatchDataAPIRouter().route()
