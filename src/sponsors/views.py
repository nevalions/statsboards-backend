from fastapi import HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SponsorServiceDB
from .schemas import SponsorSchemaCreate, SponsorSchema, SponsorSchemaUpdate, UploadSponsorLogoResponse
from src.core.config import uploads_path
from src.helpers.file_service import file_service


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

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorSchema,
        )
        async def create_sponsor_endpoint(item: SponsorSchemaCreate):
            new_ = await self.service.create_sponsor(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=SponsorSchema,
        )
        async def update_sponsor_endpoint(
                item_id: int,
                item: SponsorSchemaUpdate,
        ):
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

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sponsor_by_id_endpoint(
                item_id,
                item=Depends(self.service.get_by_id),
        ):
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

        @router.post("/upload_logo", response_model=UploadSponsorLogoResponse)
        async def upload_sponsor_logo_endpoint(file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder='sponsors/logos')
            print(uploads_path)
            return {"logoUrl": file_location}

        return router


api_sponsor_router = SponsorAPIRouter(SponsorServiceDB(db)).route()
