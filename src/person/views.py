from fastapi import HTTPException, UploadFile, File

from src.core import BaseRouter, db
from .db_services import PersonServiceDB
from .schemas import PersonSchema, PersonSchemaCreate, PersonSchemaUpdate, UploadPersonPhotoResponse, \
    UploadResizePersonPhotoResponse
from ..core.config import uploads_path
from ..helpers.file_service import file_service


# Person backend
class PersonAPIRouter(BaseRouter[PersonSchema, PersonSchemaCreate, PersonSchemaUpdate]):
    def __init__(self, service: PersonServiceDB):
        super().__init__("/api/persons", ["persons"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PersonSchema,
        )
        async def create_person_endpoint(
                person: PersonSchemaCreate,
        ):
            print(f"Received person: {person}")
            new_person = await self.service.create_or_update_person(person)
            if new_person:
                return new_person.__dict__
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Person creation fail"
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PersonSchema,
        )
        async def get_person_by_eesl_id_endpoint(
                person_eesl_id: int,
        ):
            tournament = await self.service.get_person_by_eesl_id(value=person_eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({person_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PersonSchema,
        )
        async def update_person_endpoint(
                item_id: int,
                item: PersonSchemaUpdate,
        ):
            update_ = await self.service.update_person(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Person id {item_id} not found"
                )
            return update_.__dict__

        @router.post("/upload_photo", response_model=UploadPersonPhotoResponse)
        async def upload_person_photo_endpoint(file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder='persons/photos')
            print(uploads_path)
            return {"photoUrl": file_location}

        @router.post("/upload_resize_photo", response_model=UploadResizePersonPhotoResponse)
        async def upload_and_resize_person_photo_endpoint(file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder='persons/photos',
                icon_height=100,
                web_view_height=400,
            )
            print(uploads_path)
            return uploaded_paths

        return router


api_person_router = PersonAPIRouter(PersonServiceDB(db)).route()
