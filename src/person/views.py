from fastapi import HTTPException, UploadFile, File

from src.core import BaseRouter, db
from .db_services import PersonServiceDB
from .schemas import (
    PersonSchema,
    PersonSchemaCreate,
    PersonSchemaUpdate,
    UploadPersonPhotoResponse,
    UploadResizePersonPhotoResponse,
)
from ..core.config import uploads_path
from ..helpers.file_service import file_service
from ..logging_config import get_logger, setup_logging

setup_logging()


class PersonAPIRouter(BaseRouter[PersonSchema, PersonSchemaCreate, PersonSchemaUpdate]):
    def __init__(self, service: PersonServiceDB):
        super().__init__("/api/persons", ["persons"], service)
        self.logger = get_logger("backend_logger_PersonAPIRouter", self)
        self.logger.debug(f"Initialized PersonAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PersonSchema,
        )
        async def create_person_endpoint(
            person: PersonSchemaCreate,
        ):
            self.logger.debug(f"Create or update person endpoint got data: {person}")
            new_person = await self.service.create_or_update_person(person)
            if new_person:
                return PersonSchema.model_validate(new_person)
            else:
                self.logger.error(
                    f"Error on create or update person got data: {person}"
                )
                raise HTTPException(status_code=409, detail=f"Person creation fail")

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PersonSchema,
        )
        async def get_person_by_eesl_id_endpoint(
            eesl_id: int,
        ):
            self.logger.debug(f"Get person by eesl_id: {eesl_id}")
            person = await self.service.get_person_by_eesl_id(
                value=eesl_id
            )
            if person is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Person eesl_id({eesl_id}) not found",
                )
            return PersonSchema.model_validate(person)

        @router.put(
            "/{item_id}/",
            response_model=PersonSchema,
        )
        async def update_person_endpoint(
            item_id: int,
            item: PersonSchemaUpdate,
        ):
            self.logger.debug(f"Update person endpoint got data: {item}")
            try:
                update_ = await self.service.update(item_id, item)
            except HTTPException:
                raise
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Person id {item_id} not found"
                )
            return PersonSchema.model_validate(update_)

        @router.post("/upload_photo", response_model=UploadPersonPhotoResponse)
        async def upload_person_photo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug(f"Upload person photo got data")
                file_location = await file_service.save_upload_image(
                    file, sub_folder="persons/photos"
                )
                return {"photoUrl": file_location}
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error on upload person photo got data: {ex}", exc_info=ex
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading person photo",
                )

        @router.post(
            "/upload_resize_photo", response_model=UploadResizePersonPhotoResponse
        )
        async def upload_and_resize_person_photo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug(f"Upload and resize person photo")
                uploaded_paths = await file_service.save_and_resize_upload_image(
                    file,
                    sub_folder="persons/photos",
                    icon_height=100,
                    web_view_height=400,
                )
                return uploaded_paths
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error on upload and resize photo: {ex}", exc_info=ex
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading and resizing person photo",
                )

        return router


api_person_router = PersonAPIRouter(PersonServiceDB(db)).route()
