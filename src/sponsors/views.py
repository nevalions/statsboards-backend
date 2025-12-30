from fastapi import File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from src.helpers.file_service import file_service

from ..logging_config import get_logger, setup_logging
from .db_services import SponsorServiceDB
from .schemas import (
    SponsorSchema,
    SponsorSchemaCreate,
    SponsorSchemaUpdate,
    UploadSponsorLogoResponse,
)

setup_logging()


class SponsorAPIRouter(
    BaseRouter[
        SponsorSchema,
        SponsorSchemaCreate,
        SponsorSchemaUpdate,
    ]
):
    def __init__(self, service: SponsorServiceDB):
        super().__init__(
            "/api/sponsors",
            ["sponsors"],
            service,
        )
        self.logger = get_logger("backend_logger_SponsorAPIRouter", self)
        self.logger.debug("Initialized SponsorAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorSchema,
        )
        async def create_sponsor_endpoint(item: SponsorSchemaCreate):
            self.logger.debug("Creating sponsor endpoint")
            new_ = await self.service.create(item)
            if new_ is None:
                raise HTTPException(
                    status_code=409,
                    detail="Failed to create sponsor. Check input data.",
                )
            return SponsorSchema.model_validate(new_)

        @router.put(
            "/",
            response_model=SponsorSchema,
        )
        async def update_sponsor_endpoint(
            item_id: int,
            item: SponsorSchemaUpdate,
        ):
            self.logger.debug("Updating sponsor endpoint")
            update_ = await self.service.update(
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
        async def get_sponsor_by_id_endpoint(item_id: int):
            self.logger.debug(f"Getting sponsor endpoint by id: {item_id}")
            item = await self.service.get_by_id(item_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sponsor id:{item_id} not found",
                )
            return self.create_response(
                item,
                f"Sponsor ID:{item.id}",
                "Sponsor",
            )

        @router.post("/upload_logo", response_model=UploadSponsorLogoResponse)
        async def upload_sponsor_logo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug("Uploading sponsor logo endpoint")
                file_location = await file_service.save_upload_image(
                    file, sub_folder="sponsors/logos"
                )
                return {"logoUrl": file_location}
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error saving sponsor logo: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading sponsor logo",
                )

        return router


api_sponsor_router = SponsorAPIRouter(SponsorServiceDB(db)).route()
