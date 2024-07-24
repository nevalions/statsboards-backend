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
        PlayClockSchema,
        PlayClockSchemaCreate,
        PlayClockSchemaUpdate,
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

        return router


api_playclock_router = PlayClockRouter(PlayClockServiceDB(db)).route()
