import asyncio

import fastapi.routing
from fastapi import (
    HTTPException,
    Depends,
    Path,
    Query,
    status,
    Request,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse

from src.core import BaseRouter, db
from .db_services import MatchDataServiceDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate, MatchDataSchema


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
            "/id/{match_data_id}/gameclock/running/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            background_tasks: BackgroundTasks,
            match_data_id: int,
        ):
            start_game = "in-progress"
            await self.service.update(
                match_data_id,
                MatchDataSchemaUpdate(
                    game_status=start_game,
                ),
            )
            tasks = [
                self.service.enable_match_data_gameclock_queues(match_data_id),
                self.service.clock_manager.start_clock(
                    match_data_id,
                    "game",
                ),
            ]

            await asyncio.gather(*tasks)

            item_status = "running"
            match_data = await self.service.get_by_id(match_data_id)
            present_gameclock_status = match_data.gameclock_status

            if present_gameclock_status != "running":
                updated = await self.service.update(
                    match_data_id,
                    MatchDataSchemaUpdate(
                        gameclock_status=item_status,
                    ),
                )

                await self.service.decrement_gameclock(
                    background_tasks,
                    match_data_id,
                )

                return self.create_response(
                    updated,
                    f"Game clock Match Data ID:{match_data_id} {item_status}",
                )
            else:
                return self.create_response(
                    match_data,
                    f"Game clock Match Data ID:{match_data_id} already {present_gameclock_status}",
                )

        @router.put(
            "/id/{item_id}/gameclock/paused/",
            response_class=JSONResponse,
        )
        async def pause_gameclock_endpoint(
            item_id: int,
        ):
            item_status = "paused"

            updated_ = await self.service.update(
                item_id,
                MatchDataSchemaUpdate(gameclock_status=item_status),
            )
            if updated_:
                return self.create_response(
                    updated_,
                    f"Game clock ID:{item_id} {item_status}",
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
            await self.service.update(
                item_id,
                MatchDataSchemaUpdate(
                    gameclock=sec,
                    gameclock_status=item_status,
                    game_status="stopping",
                ),
            )

            await self.service.trigger_update_match_data_gameclock_sse(item_id)

            updated = await self.service.update(
                item_id,
                MatchDataSchemaUpdate(
                    gameclock=sec,
                    gameclock_status=item_status,
                    game_status="stopped",
                ),
            )

            await self.service.trigger_update_match_data_gameclock_sse(item_id)

            return self.create_response(
                updated,
                f"Game clock {item_status}",
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
            item_status = "running"
            item = await self.service.get_by_id(item_id)
            present_playclock_status = item.playclock_status
            print(present_playclock_status)
            await self.service.enable_match_data_playclock_queues(item_id)
            # await self.service.clock_manager.start_clock(item_id, "play")
            if present_playclock_status != "running":
                await self.service.update(
                    item_id,
                    MatchDataSchemaUpdate(
                        playclock=sec,
                        playclock_status=item_status,
                    ),
                )
                await self.service.decrement_playclock(
                    background_tasks,
                    item_id,
                )
                # await self.service.trigger_update_match_data_playclock(item_id)

                return self.create_response(
                    item,
                    f"Play clock ID:{item_id} {item_status}",
                )
            else:
                return self.create_response(
                    item,
                    f"Play clock ID:{item_id} already {present_playclock_status}",
                )

        @router.put(
            "/id/{item_id}/playclock/stopped/",
            response_class=JSONResponse,
        )
        async def reset_playclock_endpoint(
            item_id: int,
        ):
            item_status = "stopped"
            updated = await self.service.update(
                item_id,
                MatchDataSchemaUpdate(
                    playclock=None,
                    playclock_status=item_status,
                ),
            )
            await self.service.trigger_update_match_data_playclock(item_id)
            return self.create_response(
                updated,
                f"Play clock {item_status}",
            )

        @router.get("/events/")
        async def sse_match_data_endpoint(request: Request):
            return StreamingResponse(
                self.service.event_generator_match_data(),
                media_type="text/event-stream",
            )

        @router.get("/id/{match_data_id}/events/playclock/")
        async def sse_match_data_playclock_endpoint(match_data_id: int):
            return StreamingResponse(
                self.service.event_generator_get_match_data_playclock(match_data_id),
                media_type="text/event-stream",
            )

        @router.get("/id/{match_data_id}/events/gameclock/")
        async def sse_match_data_gameclock_endpoint(match_data_id: int):
            return StreamingResponse(
                self.service.event_generator_get_match_data_gameclock(match_data_id),
                media_type="text/event-stream",
            )

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


api_matchdata_router = MatchDataRouter(MatchDataServiceDB(db)).route()
