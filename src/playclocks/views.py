from fastapi import (
    HTTPException,
    Depends,
    status,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import PlayClockServiceDB
from .schemas import PlayClockSchema, PlayClockSchemaCreate, PlayClockSchemaUpdate


class PlayClockRouter(
    BaseRouter[
        PlayClockSchema, PlayClockSchemaCreate, PlayClockSchemaUpdate,
    ]
):
    def __init__(self, service: PlayClockServiceDB):
        super().__init__(
            "/api/playclock",
            ["playclock"],
            service,
        )

    def route(self):
        router = super().route()

        # Playclock backend
        @router.post(
            "/",
            response_model=PlayClockSchema,
        )
        async def create_playclock_endpoint(playclock: PlayClockSchemaCreate):
            new_playclock = await self.service.create_playclock(playclock)
            return new_playclock.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PlayClockSchema,
        )
        async def update_playclock_(
                item_id: int,
                playclock: PlayClockSchemaUpdate,
        ):
            playclock_update = await self.service.update_playclock(
                item_id,
                playclock,
            )

            if playclock_update is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Playclock " f"id({item_id}) " f"not found",
                )
            return playclock_update

        @router.put(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def update_playclock_by_id(
                item_id: int,
                item=Depends(update_playclock_),
        ):
            if item:
                return {
                    "content": item.__dict__,
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"Playclock id:{item_id} not found",
            )

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_playclock_by_id(
                item=Depends(self.service.get_by_id),
        ):
            return self.create_response(
                item,
                f"Playclock ID:{item.id}",
                "playclock",
            )

        # @router.put(
        #     "/id/{match_data_id}/gameclock/running/",
        #     response_class=JSONResponse,
        # )
        # async def start_gameclock_endpoint(
        #         background_tasks: BackgroundTasks,
        #         match_data_id: int,
        # ):
        #     start_game = "in-progress"
        #     await self.service.update(
        #         match_data_id,
        #         MatchDataSchemaUpdate(
        #             game_status=start_game,
        #         ),
        #     )
        #     tasks = [
        #         self.service.enable_match_data_clock_queues(
        #             match_data_id,
        #             "game",
        #         ),
        #         # self.service.clock_manager.start_clock(
        #         #     match_data_id,
        #         #     "game",
        #         # ),
        #     ]
        #
        #     await asyncio.gather(*tasks)
        #
        #     item_status = "running"
        #     match_data = await self.service.get_by_id(match_data_id)
        #     present_gameclock_status = match_data.gameclock_status
        #
        #     if present_gameclock_status != "running":
        #         updated = await self.service.update(
        #             match_data_id,
        #             MatchDataSchemaUpdate(
        #                 gameclock_status=item_status,
        #             ),
        #         )
        #
        #         await self.service.decrement_gameclock(
        #             background_tasks,
        #             match_data_id,
        #         )
        #
        #         return self.create_response(
        #             updated,
        #             f"Game clock Match Data ID:{match_data_id} {item_status}",
        #         )
        #     else:
        #         return self.create_response(
        #             match_data,
        #             f"Game clock Match Data ID:{match_data_id} already {present_gameclock_status}",
        #         )

        # @router.put(
        #     "/id/{item_id}/gameclock/paused/",
        #     response_class=JSONResponse,
        # )
        # async def pause_gameclock_endpoint(
        #         item_id: int,
        # ):
        #     item_status = "paused"
        #
        #     updated_ = await self.service.update(
        #         item_id,
        #         MatchDataSchemaUpdate(gameclock_status=item_status),
        #     )
        #     if updated_:
        #         return self.create_response(
        #             updated_,
        #             f"Game clock ID:{item_id} {item_status}",
        #         )
        #
        # @router.put(
        #     "/id/{item_id}/gameclock/{item_status}/{sec}/",
        #     response_class=JSONResponse,
        # )
        # async def reset_gameclock_endpoint(
        #         item_id: int,
        #         item_status: str = Path(
        #             ...,
        #             example="stopped",
        #         ),
        #         sec: int = Path(
        #             ...,
        #             description="Seconds",
        #             example=720,
        #         ),
        # ):
        #     await self.service.update(
        #         item_id,
        #         MatchDataSchemaUpdate(
        #             gameclock=sec,
        #             gameclock_status=item_status,
        #             game_status="stopping",
        #         ),
        #     )
        #
        #     await self.service.trigger_update_match_clock(item_id, "game")
        #
        #     updated = await self.service.update(
        #         item_id,
        #         MatchDataSchemaUpdate(
        #             gameclock=sec,
        #             gameclock_status=item_status,
        #             game_status="stopped",
        #         ),
        #     )
        #
        #     await self.service.trigger_update_match_clock(item_id, "game")
        #
        #     return self.create_response(
        #         updated,
        #         f"Game clock {item_status}",
        #     )

        @router.put(
            "/id/{item_id}/running/{sec}/",
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

            await self.service.enable_match_data_clock_queues(item_id)
            if present_playclock_status != "running":
                await self.service.update(
                    item_id,
                    PlayClockSchemaUpdate(
                        playclock=sec,
                        playclock_status=item_status,
                    ),
                )
                await self.service.decrement_playclock(
                    background_tasks,
                    item_id,
                )

                return self.create_response(
                    item,
                    f"Playclock ID:{item_id} {item_status}",
                )
            else:
                return self.create_response(
                    item,
                    f"Playclock ID:{item_id} already {present_playclock_status}",
                )

        @router.put(
            "/id/{item_id}/stopped/",
            response_class=JSONResponse,
        )
        async def reset_playclock_endpoint(
                item_id: int,
        ):
            item_status = "stopped"

            # await self.service.update(
            #     item_id,
            #     PlayClockSchemaUpdate(
            #         playclock=None,
            #         playclock_status="stopping",
            #     ),
            # )
            #
            # await self.service.trigger_update_playclock(item_id)

            updated = await self.service.update(
                item_id,
                PlayClockSchemaUpdate(
                    playclock=None,
                    playclock_status="stopped",
                ),
            )

            return self.create_response(
                updated,
                f"Play clock {item_status}",
            )

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


api_playclock_router = PlayClockRouter(PlayClockServiceDB(db)).route()
