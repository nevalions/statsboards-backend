from fastapi import HTTPException, Depends, Path, Query, status, Request
from fastapi.responses import JSONResponse, StreamingResponse

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
            "/id/{item_id}/gameclock/running/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            item_id: int,
        ):
            item_status = "running"
            item = await self.service.get_by_id(item_id)
            present_gameclock_status = item.gameclock_status
            if present_gameclock_status != "running":
                updated = await self.service.update_match_data(
                    item_id,
                    MatchDataSchemaUpdate(gameclock_status=item_status),
                )
                await self.service.decrement_gameclock(item_id)

                return self.create_response(
                    updated,
                    f"Game clock ID:{item_id} {item_status}",
                )
            else:
                return self.create_response(
                    item,
                    f"Game clock ID:{item_id} already {present_gameclock_status}",
                )

        @router.put(
            "/id/{item_id}/gameclock/paused/",
            response_class=JSONResponse,
        )
        async def start_gameclock_endpoint(
            item_id: int,
        ):
            item_status = "paused"

            updated_ = await self.service.update_match_data(
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
            updated = await self.service.update_match_data(
                item_id,
                MatchDataSchemaUpdate(
                    gameclock=sec,
                    gameclock_status=item_status,
                ),
            )
            # await trigger_update(item_id)
            return self.create_response(
                updated,
                f"Game clock {item_status}",
            )

        @router.get("/events/")
        async def sse_match_data_endpoint(request: Request):
            return StreamingResponse(
                self.service.event_generator_match_data(),
                media_type="text/event-stream",
            )

        return router


api_matchdata_router = MatchDataRouter(MatchDataServiceDB(db)).route()
