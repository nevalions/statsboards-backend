from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db

from ..logging_config import get_logger, setup_logging
from .db_services import SponsorLineServiceDB
from .schemas import SponsorLineSchema, SponsorLineSchemaCreate, SponsorLineSchemaUpdate

setup_logging()


class SponsorLineAPIRouter(
    BaseRouter[
        SponsorLineSchema,
        SponsorLineSchemaCreate,
        SponsorLineSchemaUpdate,
    ]
):
    def __init__(self, service: SponsorLineServiceDB):
        super().__init__(
            "/api/sponsor_lines",
            ["sponsor_lines"],
            service,
        )
        self.logger = get_logger("backend_logger_SponsorLineAPIRouter", self)
        self.logger.debug("Initialized SponsorLineAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorLineSchema,
        )
        async def create_sponsor_line_endpoint(item: SponsorLineSchemaCreate):
            try:
                self.logger.debug("Create sponsor line endpoint")
                new_ = await self.service.create(item)
                return SponsorLineSchema.model_validate(new_)
            except Exception as e:
                self.logger.error(
                    f"Error creating sponsor line endpoint {e}", exc_info=True
                )

        @router.put(
            "/",
            response_model=SponsorLineSchema,
        )
        async def update_sponsor_line_endpoint(
            item_id: int,
            item: SponsorLineSchemaUpdate,
        ):
            self.logger.debug("Update sponsor line endpoint")
            try:
                update_ = await self.service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"SponsorLine id:{item_id} not found",
                    )
                return SponsorLineSchema.model_validate(update_)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error updating sponsor line endpoint {e}", exc_info=True
                )
                raise HTTPException(
                    status_code=409,
                    detail="Error updating sponsor line",
                )

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sponsor_line_by_id_endpoint(item_id: int):
            try:
                self.logger.debug(f"Get sponsor line endpoint by id {item_id}")
                item = await self.service.get_by_id(item_id)
                if item:
                    return self.create_response(
                        item,
                        f"SponsorLine ID:{item.id}",
                        "SponsorLine",
                    )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"SponsorLine id:{item_id} not found",
                    )
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error getting sponsor line endpoint {e} by id:{item_id}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error retrieving sponsor line",
                )

        return router


api_sponsor_line_router = SponsorLineAPIRouter(SponsorLineServiceDB(db)).route()
