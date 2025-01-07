from fastapi import HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SponsorServiceDB
from .schemas import (
    SponsorSchemaCreate,
    SponsorSchema,
    SponsorSchemaUpdate,
    UploadSponsorLogoResponse,
)
from src.core.config import uploads_path
from src.helpers.file_service import file_service
from ..logging_config import setup_logging, get_logger

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
        self.logger.debug(f"Initialized SponsorAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorSchema,
        )
        async def create_sponsor_endpoint(item: SponsorSchemaCreate):
            try:
                self.logger.debug(f"Creating sponsor endpoint")
                new_ = await self.service.create_sponsor(item)
                return new_.__dict__
            except Exception as e:
                self.logger.error(
                    f"Error creating sponsor endpoint: {e}", exc_info=True
                )

        @router.put(
            "/",
            response_model=SponsorSchema,
        )
        async def update_sponsor_endpoint(
            item_id: int,
            item: SponsorSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Updating sponsor endpoint")
                update_ = await self.service.update_sponsor(
                    item_id,
                    item,
                )
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Sponsor id:{item_id} not found",
                    )
                return update_.__dict__
            except Exception as e:
                self.logger.error(
                    f"Error updating sponsor endpoint: {e}", exc_info=True
                )

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sponsor_by_id_endpoint(
            item_id,
            item=Depends(self.service.get_by_id),
        ):
            try:
                self.logger.debug(f"Getting sponsor endpoint by id: {item_id}")
                if item:
                    return self.create_response(
                        item,
                        f"Sponsor ID:{item.id}",
                        "Sponsor",
                    )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Sponsor id:{item_id} not found",
                    )
            except Exception as e:
                self.logger.error(
                    f"Error getting sponsor endpoint by id:{item_id} {e}", exc_info=True
                )

        @router.post("/upload_logo", response_model=UploadSponsorLogoResponse)
        async def upload_sponsor_logo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug(f"Uploading sponsor logo endpoint")
                file_location = await file_service.save_upload_image(
                    file, sub_folder="sponsors/logos"
                )
                return {"logoUrl": file_location}
            except Exception as e:
                self.logger.error(f"Error saving sponsor logo: {e}", exc_info=True)

        return router


api_sponsor_router = SponsorAPIRouter(SponsorServiceDB(db)).route()
