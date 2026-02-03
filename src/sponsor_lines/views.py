from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import SponsorLineService
from src.core.models import SponsorLineDB, handle_view_exceptions

from ..logging_config import get_logger
from .schemas import SponsorLineSchema, SponsorLineSchemaCreate, SponsorLineSchemaUpdate


class SponsorLineAPIRouter(
    BaseRouter[
        SponsorLineSchema,
        SponsorLineSchemaCreate,
        SponsorLineSchemaUpdate,
    ]
):
    def __init__(self, service_name: str | None = None):
        super().__init__(
            "/api/sponsor_lines",
            ["sponsor_lines"],
            None,
            service_name=service_name,
        )
        self.logger = get_logger("SponsorLineAPIRouter", self)
        self.logger.debug("Initialized SponsorLineAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorLineSchema,
        )
        @handle_view_exceptions(error_message="Error creating sponsor line", status_code=500)
        async def create_sponsor_line_endpoint(
            sponsor_line_service: SponsorLineService, item: SponsorLineSchemaCreate
        ):
            self.logger.debug("Create sponsor line endpoint")
            new_ = await sponsor_line_service.create(item)
            if new_ is None:
                raise HTTPException(
                    status_code=409,
                    detail="Failed to create sponsor line. Check input data.",
                )
            return SponsorLineSchema.model_validate(new_)

        @router.put(
            "/{item_id}/",
            response_model=SponsorLineSchema,
        )
        async def update_sponsor_line_endpoint(
            sponsor_line_service: SponsorLineService,
            item_id: int,
            item: SponsorLineSchemaUpdate,
        ):
            self.logger.debug("Update sponsor line endpoint")
            update_ = await sponsor_line_service.update(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"SponsorLine id:{item_id} not found",
                )
            return SponsorLineSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_model=SponsorLineSchema,
        )
        async def get_sponsor_line_by_id_endpoint(
            sponsor_line_service: SponsorLineService, item_id: int
        ):
            try:
                self.logger.debug(f"Get sponsor line endpoint by id {item_id}")
                item = await sponsor_line_service.get_by_id(item_id)
                if item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"SponsorLine id:{item_id} not found",
                    )
                return SponsorLineSchema.model_validate(item)
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
                ) from e

        @router.delete(
            "/id/{model_id}",
            summary="Delete sponsor line",
            description="Delete a sponsor line by ID. Requires admin role.",
            responses={
                200: {"description": "SponsorLine deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "SponsorLine not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_sponsor_line_endpoint(
            sponsor_line_service: SponsorLineService,
            model_id: int,
            _: Annotated[SponsorLineDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete sponsor line endpoint id:{model_id}")
            await sponsor_line_service.delete(model_id)
            return {"detail": f"SponsorLine {model_id} deleted successfully"}

        return router


api_sponsor_line_router = SponsorLineAPIRouter().route()
