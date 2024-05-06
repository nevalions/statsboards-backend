from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PositionServiceDB
from .schemas import PositionSchema, PositionSchemaCreate, PositionSchemaUpdate


# Position backend
class PositionAPIRouter(BaseRouter[PositionSchema, PositionSchemaCreate, PositionSchemaUpdate]):
    def __init__(self, service: PositionServiceDB):
        super().__init__("/api/positions", ["positions"], service)

    def route(self):
        router = super().route()

        @router.post("/", response_model=PositionSchema)
        async def create_position_endpoint(
                position: PositionSchemaCreate,
        ):
            # print(f"Received position: {position}")
            new_position = await self.service.create_new_position(position)
            return new_position.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PositionSchema,
        )
        async def update_position_endpoint(
                item_id: int,
                item: PositionSchemaUpdate,
        ):
            update_ = await self.service.update_position(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Position id {item_id} not found"
                )
            return update_.__dict__

        @router.get(
            "/title/{item_title}/",
            response_model=PositionSchema,
        )
        async def get_position_by_title_endpoint(
                item_title: str
        ):
            return await self.service.get_position_by_title(item_title)

        return router


api_position_router = PositionAPIRouter(PositionServiceDB(db)).route()
