import asyncio

from fastapi import (
    HTTPException,
    Depends,
    Path,
    status,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import MatchDataServiceDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate, MatchDataSchema
from ..logging_config import setup_logging, get_logger

setup_logging()


class MatchDataAPIRouter(
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
        self.logger = get_logger("backend_logger_MatchDataAPIRouter", self)
        self.logger.debug(f"Initialized MatchDataAPIRouter")

    def route(self):
        router = super().route()

        # Match data backend
        @router.post(
            "/",
            response_model=MatchDataSchema,
        )
        async def create_match_data(match_data: MatchDataSchemaCreate):
            self.logger.debug(f"Create matchdata endpoint got data: {match_data}")
            try:
                new_match_data = await self.service.create_match_data(match_data)
                return new_match_data.__dict__
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
            item_id: int,
            match_data: MatchDataSchemaUpdate,
        ):
            self.logger.debug(
                f"Update matchdata endpoint id:{item_id} data: {match_data}"
            )
            try:
                match_data_update = await self.service.update_match_data(
                    item_id,
                    match_data,
                )

                if match_data_update is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Matchdata id({item_id}) not found",
                    )
                return match_data_update
            except Exception as ex:
                self.logger.error(
                    f"Error updating matchdata with data: {match_data} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"Error updating matchdata with data",
                )

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_matchdata_by_id(
            item_id: int,
            item=Depends(update_match_data_),
        ):
            self.logger.debug(f"Update matchdata by ID")
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
            self.logger.debug(f"Get matchdata by id endpoint")
            return self.create_response(
                item,
                f"MatchData ID:{item.id}",
                "matchData",
            )

        @router.put(
            "/id/{match_data_id}/gameclock/running/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            background_tasks: BackgroundTasks,
            match_data_id: int,
        ):
            self.logger.debug(f"Start gameclock endpoint")

            try:
                start_game = "in-progress"
                self.logger.debug(f"Start gameclock with matchdata id: {match_data_id}")
                await self.service.update(
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
                self.service.enable_match_data_clock_queues(
                    match_data_id,
                    "game",
                ),
            ]
            self.logger.debug(f"Enabled tasks {tasks}")

            await asyncio.gather(*tasks)

            item_status = "running"
            try:
                self.logger.debug(f"Start gameclock with matchdata id: {match_data_id}")
                match_data = await self.service.get_by_id(match_data_id)
                present_gameclock_status = match_data.gameclock_status
                self.logger.debug(
                    f"Present gameclock status: {present_gameclock_status}"
                )

                if present_gameclock_status != "running":
                    self.logger.debug("Gameclock not running")
                    updated = await self.service.update(
                        match_data_id,
                        MatchDataSchemaUpdate(
                            gameclock_status=item_status,
                        ),
                    )

                    self.logger.debug(f"Go to decrement gameclock")
                    await self.service.decrement_gameclock(
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
            item_id: int,
        ):
            self.logger.debug(f"Pause gameclock endpoint")
            item_status = "paused"
            try:
                updated_ = await self.service.update(
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
                self.logger.error(
                    f"Error pausing gameclock id: {item_id} {ex}", exc_info=True
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
            try:
                self.logger.debug(f"Reset gameclock endpoint")
                await self.service.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        gameclock=sec,
                        gameclock_status=item_status,
                        game_status="stopping",
                    ),
                )
            except Exception as ex:
                self.logger.error(
                    f"Error updating gameclock id: {item_id} {ex}", exc_info=True
                )

            # await self.service.trigger_update_match_clock(item_id, "game")

            try:
                updated = await self.service.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        gameclock=sec,
                        gameclock_status=item_status,
                        game_status="stopped",
                    ),
                )

                # await self.service.trigger_update_match_clock(item_id, "game")
                self.logger.debug(f"Game clock id:{item_id} {item_status}")
                return self.create_response(
                    updated,
                    f"Game clock {item_status}",
                )
            except Exception as ex:
                self.logger.error(
                    f"Error while reset gameclock id: {item_id} {ex}", exc_info=True
                )

        @router.put(
            "/id/{item_id}/playclock/running/{sec}/",
            response_class=JSONResponse,
        )
        async def start_playclock_endpoint(
            background_tasks: BackgroundTasks,
            item_id: int,
            sec: int,
        ):
            self.logger.debug(f"Start playclock endpoint")
            item_status = "running"

            try:
                item = await self.service.get_by_id(item_id)
                present_playclock_status = item.playclock_status

                await self.service.enable_match_data_clock_queues(
                    item_id,
                    "play",
                )
                if present_playclock_status != "running":
                    self.logger.debug(f"Playclock not running")
                    await self.service.update(
                        item_id,
                        MatchDataSchemaUpdate(
                            playclock=sec,
                            playclock_status=item_status,
                        ),
                    )

                    self.logger.debug(f"Go to decrement playclock")
                    await self.service.decrement_playclock(
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
            item_id: int,
        ):
            item_status = "stopped"
            self.logger.debug(f"Reset playclock id{item_id} endpoint")

            await self.service.update(
                item_id,
                MatchDataSchemaUpdate(
                    playclock=None,
                    playclock_status="stopping",
                ),
            )

            # await self.service.trigger_update_match_clock(item_id, "play")

            updated = await self.service.update(
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
        #         self.service.event_generator_get_match_data(match_data_id),
        #         media_type="text/event-stream",
        #     )
        #
        # @router.get("/id/{match_data_id}/events/playclock/")
        # async def sse_match_data_playclock_endpoint(match_data_id: int):
        #     return StreamingResponse(
        #         self.service.event_generator_get_match_clock(
        #             match_data_id,
        #             "play",
        #         ),
        #         media_type="text/event-stream",
        #     )
        #
        # @router.get("/id/{match_data_id}/events/gameclock/")
        # async def sse_match_data_gameclock_endpoint(match_data_id: int):
        #     return StreamingResponse(
        #         self.service.event_generator_get_match_clock(
        #             match_data_id,
        #             "game",
        #         ),
        #         media_type="text/event-stream",
        #     )

        # @router.get("/id/{match_data_id}/events/gameclock/")
        # async def sse_match_data_gameclock_endpoint(match_data_id: int):
        #
        #     await self.service.enable_match_data_events_queues(match_data_id)
        #
        #     return StreamingResponse(
        #         self.service.event_generator_get_match_data_gameclock(
        #             match_data_id
        #         ),
        #         media_type="text/event-stream",
        #     )

        # @router.get(
        #     "/queue/",
        #     response_class=JSONResponse,
        # )
        # async def queue():
        #     return await self.service.get_active_match_ids()

        return router


api_matchdata_router = MatchDataAPIRouter(MatchDataServiceDB(db)).route()
