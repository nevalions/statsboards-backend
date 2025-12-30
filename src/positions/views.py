from fastapi import HTTPException

from src.core import BaseRouter, db

from ..logging_config import get_logger, setup_logging
from .db_services import PositionServiceDB
from .schemas import PositionSchema, PositionSchemaCreate, PositionSchemaUpdate

setup_logging()


class PositionAPIRouter(
    BaseRouter[PositionSchema, PositionSchemaCreate, PositionSchemaUpdate]
):
    def __init__(self, service: PositionServiceDB):
        super().__init__("/api/positions", ["positions"], service)
        self.logger = get_logger("backend_logger_PositionAPIRouter", self)
        self.logger.debug("Initialized PositionAPIRouter")

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
                new_position = await self.service.create(position)
                if new_position:
                    return PositionSchema.model_validate(new_position)
                else:
                    self.logger.error(f"Error on create position got data: {position}")
                    raise HTTPException(
                        status_code=409, detail="Position creation fail"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error on create position got data: {position} {e}", exc_info=True
                )
                raise

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
                update_ = await self.service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404, detail=f"Position id {item_id} not found"
                    )
                return PositionSchema.model_validate(update_)
            except Exception as ex:
                self.logger.error(
                    f"Error on update postion, got data: {ex}", exc_info=ex
                )
                raise

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
                raise

        return router


api_position_router = PositionAPIRouter(PositionServiceDB(db)).route()
