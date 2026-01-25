from typing import Annotated

from fastapi import Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import SponsorService
from src.core.models import SponsorDB, handle_view_exceptions

from ..logging_config import get_logger
from .schemas import (
    PaginatedSponsorResponse,
    SponsorSchema,
    SponsorSchemaCreate,
    SponsorSchemaUpdate,
    UploadSponsorLogoResponse,
)


class SponsorAPIRouter(
    BaseRouter[
        SponsorSchema,
        SponsorSchemaCreate,
        SponsorSchemaUpdate,
    ]
):
    def __init__(self):
        super().__init__(
            "/api/sponsors",
            ["sponsors"],
            None,
        )
        self.logger = get_logger("backend_logger_SponsorAPIRouter", self)
        self.logger.debug("Initialized SponsorAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorSchema,
        )
        async def create_sponsor_endpoint(
            sponsor_service: SponsorService,
            item: SponsorSchemaCreate,
        ):
            self.logger.debug("Creating sponsor endpoint")
            new_ = await sponsor_service.create(item)
            if new_ is None:
                raise HTTPException(
                    status_code=409,
                    detail="Failed to create sponsor. Check input data.",
                )
            return SponsorSchema.model_validate(new_)

        @router.put(
            "/{item_id}/",
            response_model=SponsorSchema,
        )
        async def update_sponsor_endpoint(
            sponsor_service: SponsorService,
            item_id: int,
            item: SponsorSchemaUpdate,
        ):
            self.logger.debug("Updating sponsor endpoint")
            update_ = await sponsor_service.update(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sponsor with id {item_id} not found",
                )
            return SponsorSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sponsor_by_id_endpoint(sponsor_service: SponsorService, item_id: int):
            self.logger.debug(f"Getting sponsor endpoint by id: {item_id}")
            item = await sponsor_service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sponsor id:{item_id} not found",
                )
            return self.create_response(
                item,
                f"Sponsor ID:{item.id}",
                "text",
            )

        @router.post("/upload_logo", response_model=UploadSponsorLogoResponse)
        @handle_view_exceptions(
            error_message="Error uploading sponsor logo",
            status_code=500,
        )
        async def upload_sponsor_logo_endpoint(
            sponsor_service: SponsorService,
            file: UploadFile = File(...),
        ):
            self.logger.debug("Uploading sponsor logo")
            file_location = await sponsor_service.save_upload_image(
                file,
                sub_folder="sponsors/logos",
            )
            return {"logoUrl": file_location}

        @router.get(
            "/paginated",
            response_model=PaginatedSponsorResponse,
            summary="Search sponsors with pagination",
            description="Search sponsors by title with pagination and standard query parameters",
        )
        async def search_sponsors_paginated_endpoint(
            sponsor_service: SponsorService,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("title", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for title search"),
        ):
            self.logger.debug(
                f"Search sponsors paginated: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
            )
            skip = (page - 1) * items_per_page
            response = await sponsor_service.search_sponsors_with_pagination(
                search_query=search,
                skip=skip,
                limit=items_per_page,
                order_by=order_by,
                order_by_two=order_by_two,
                ascending=ascending,
            )
            return response

        @router.delete(
            "/id/{model_id}",
            summary="Delete sponsor",
            description="Delete a sponsor by ID. Requires admin role.",
            responses={
                200: {"description": "Sponsor deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Sponsor not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_sponsor_endpoint(
            sponsor_service: SponsorService,
            model_id: int,
            _: Annotated[SponsorDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete sponsor endpoint id:{model_id}")
            await sponsor_service.delete(model_id)
            return {"detail": f"Sponsor {model_id} deleted successfully"}

        return router


api_sponsor_router = SponsorAPIRouter().route()
