from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PositionServiceDB
from .schemas import PositionSchema, PositionSchemaCreate, PositionSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()


class PositionAPIRouter(
    BaseRouter[PositionSchema, PositionSchemaCreate, PositionSchemaUpdate]
):
    def __init__(self, service: PositionServiceDB):
        super().__init__("/api/positions", ["positions"], service)
        self.logger = get_logger("backend_logger_PositionAPIRouter", self)
        self.logger.debug(f"Initialized PositionAPIRouter")

    def route(self):
        router = super().route()

        @router.post("/", response_model=PositionSchema)
        async def create_position_endpoint(
            position: PositionSchemaCreate,
        ):
            try:
                self.logger.debug(
                    f"Create or update position endpoint got data: {position}"
                )
                new_position = await self.service.create_new_position(position)
                if new_position:
                    return new_position.__dict__
                else:
                    self.logger.error(f"Error on create position got data: {position}")
                    raise HTTPException(
                        status_code=409, detail=f"Position creation fail"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error on create position got data: {position} {e}", exc_info=True
                )

        @router.put(
            "/{item_id}/",
            response_model=PositionSchema,
        )
        async def update_position_endpoint(
            item_id: int,
            item: PositionSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Update position endpoint got data: {item}")
                update_ = await self.service.update_position(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404, detail=f"Position id {item_id} not found"
                    )
                return update_.__dict__
            except Exception as ex:
                self.logger.error(
                    f"Error on update postion, got data: {ex}", exc_info=ex
                )

        @router.get(
            "/title/{item_title}/",
            response_model=PositionSchema,
        )
        async def get_position_by_title_endpoint(item_title: str):
            try:
                return await self.service.get_position_by_title(item_title)
            except Exception as ex:
                self.logger.error(
                    f"Error on get position by title: {item_title}", exc_info=ex
                )

        return router


api_position_router = PositionAPIRouter(PositionServiceDB(db)).route()
