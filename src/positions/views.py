from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import PositionService
from src.core.models import PositionDB

from ..logging_config import get_logger
from .schemas import PositionSchema, PositionSchemaCreate, PositionSchemaUpdate


class PositionAPIRouter(BaseRouter[PositionSchema, PositionSchemaCreate, PositionSchemaUpdate]):
    def __init__(self):
        super().__init__("/api/positions", ["positions"], None)
        self.logger = get_logger("backend_logger_PositionAPIRouter", self)
        self.logger.debug("Initialized PositionAPIRouter")

    def route(self):
        router = super().route()

        @router.post("/", response_model=PositionSchema)
        async def create_position_endpoint(
            position_service: PositionService,
            position: PositionSchemaCreate,
        ):
            try:
                self.logger.debug(f"Create or update position endpoint got data: {position}")
                new_position = await position_service.create(position)
                if new_position:
                    return PositionSchema.model_validate(new_position)
                else:
                    self.logger.error(f"Error on create position got data: {position}")
                    raise HTTPException(status_code=409, detail="Position creation fail")
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
            position_service: PositionService,
            item_id: int,
            item: PositionSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Update position endpoint got data: {item}")
                update_ = await position_service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(status_code=404, detail=f"Position id {item_id} not found")
                return PositionSchema.model_validate(update_)
            except Exception as ex:
                self.logger.error(f"Error on update postion, got data: {ex}", exc_info=ex)
                raise

        @router.get(
            "/",
            response_model=list[PositionSchema],
        )
        async def get_all_positions_endpoint(position_service: PositionService):
            self.logger.debug("Get all positions endpoint")
            positions = await position_service.get_all_elements()
            return [PositionSchema.model_validate(p) for p in positions]

        @router.get(
            "/id/{item_id}",
            response_model=PositionSchema,
        )
        async def get_position_by_id_endpoint(
            position_service: PositionService,
            item_id: int,
        ):
            self.logger.debug(f"Get position by id: {item_id}")
            position = await position_service.get_by_id(item_id)
            if position is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Position id {item_id} not found",
                )
            return PositionSchema.model_validate(position)

        @router.get(
            "/title/{item_title}/",
            response_model=PositionSchema,
        )
        async def get_position_by_title_endpoint(
            position_service: PositionService,
            item_title: str,
        ):
            try:
                position = await position_service.get_position_by_title(item_title)
                if position is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Position title {item_title} not found",
                    )
                return PositionSchema.model_validate(position)
            except Exception as ex:
                self.logger.error(f"Error on get position by title: {item_title}", exc_info=ex)
                raise

        @router.delete(
            "/id/{model_id}",
            summary="Delete position",
            description="Delete a position by ID. Requires admin role.",
            responses={
                200: {"description": "Position deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Position not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_position_endpoint(
            position_service: PositionService,
            model_id: int,
            _: Annotated[PositionDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete position endpoint id:{model_id}")
            await position_service.delete(model_id)
            return {"detail": f"Position {model_id} deleted successfully"}

        return router


api_position_router = PositionAPIRouter().route()
