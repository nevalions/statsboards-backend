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
from .db_services import GameClockServiceDB
from .schemas import GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate


class GameClockRouter(
    BaseRouter[
        GameClockSchema, GameClockSchemaCreate, GameClockSchemaUpdate
    ]
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
        async def start_gameclock_endpoint(background_tasks: BackgroundTasks, gameclock_id: int):
            gameclock = await self.service.get_by_id(gameclock_id)
            present_gameclock_status = gameclock.gameclock_status

            # If the gameclock was not running, then start it
            if present_gameclock_status != "running":
                # Update the gameclock status to running
                updated = await self.service.update(
                    gameclock_id,
                    GameClockSchemaUpdate(
                        gameclock_status="running",
                        gameclock_time_remaining=gameclock.gameclock,  # Initialize remaining time with game clock value
                    ),
                )

                # Start background task for decrementing the game clock
                background_tasks.add_task(self.service.loop_decrement_gameclock, gameclock_id)

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
                GameClockSchemaUpdate(
                    gameclock_status=item_status
                ),
            )
            print('updated updated')
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
                GameClockSchemaUpdate(
                    gameclock=sec,
                    gameclock_status=item_status
                ),
            )

            return self.create_response(
                updated,
                f"Game clock {item_status}",
            )

            # await self.service.trigger_update_gameclock(item_id)

            # updated = await self.service.update(
            #     item_id,
            #     GameClockSchemaUpdate(
            #         gameclock=sec,
            #         gameclock_status=item_status
            #     ),
            # )

            # await self.service.trigger_update_gameclock(item_id)

        # @router.put(
        #     "/id/{item_id}/running/{sec}/",
        #     response_class=JSONResponse,
        # )
        # async def start_playclock_endpoint(
        #         background_tasks: BackgroundTasks,
        #         item_id: int,
        #         sec: int,
        # ):
        #     item_status = "running"
        #     item = await self.service.get_by_id(item_id)
        #     present_playclock_status = item.playclock_status
        #
        #     await self.service.enable_match_data_clock_queues(item_id)
        #     if present_playclock_status != "running":
        #         await self.service.update(
        #             item_id,
        #             PlayClockSchemaUpdate(
        #                 playclock=sec,
        #                 playclock_status=item_status,
        #             ),
        #         )
        #         await self.service.decrement_playclock(
        #             background_tasks,
        #             item_id,
        #         )
        #
        #         return self.create_response(
        #             item,
        #             f"Playclock ID:{item_id} {item_status}",
        #         )
        #     else:
        #         return self.create_response(
        #             item,
        #             f"Playclock ID:{item_id} already {present_playclock_status}",
        #         )

        #
        # @router.put(
        #     "/id/{item_id}/stopped/",
        #     response_class=JSONResponse,
        # )
        # async def reset_playclock_endpoint(
        #         item_id: int,
        # ):
        #     item_status = "stopped"
        #
        #     await self.service.update(
        #         item_id,
        #         PlayClockSchemaUpdate(
        #             playclock=None,
        #             playclock_status="stopping",
        #         ),
        #     )
        #
        #     await self.service.trigger_update_playclock(item_id)
        #
        #     updated = await self.service.update(
        #         item_id,
        #         PlayClockSchemaUpdate(
        #             playclock_status="stopped",
        #         ),
        #     )
        #
        #     return self.create_response(
        #         updated,
        #         f"Play clock {item_status}",
        #     )

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


api_gameclock_router = GameClockRouter(GameClockServiceDB(db)).route()
