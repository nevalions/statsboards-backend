from typing import Annotated

from fastapi import Depends, File, HTTPException, Query, UploadFile

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.dependencies import PersonService
from src.core.models import PersonDB

from ..helpers.file_service import file_service
from ..logging_config import get_logger
from .schemas import (
    PaginatedPersonResponse,
    PersonSchema,
    PersonSchemaCreate,
    PersonSchemaUpdate,
    UploadPersonPhotoResponse,
    UploadResizePersonPhotoResponse,
)


class PersonAPIRouter(BaseRouter[PersonSchema, PersonSchemaCreate, PersonSchemaUpdate]):
    def __init__(self):
        super().__init__("/api/persons", ["persons"], None)
        self.logger = get_logger("PersonAPIRouter", self)
        self.logger.debug("Initialized PersonAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PersonSchema,
        )
        async def create_person_endpoint(
            person_service: PersonService,
            person: PersonSchemaCreate,
        ):
            self.logger.debug(f"Create or update person endpoint got data: {person}")
            new_person = await person_service.create_or_update_person(person)
            if new_person:
                return PersonSchema.model_validate(new_person)
            else:
                self.logger.error(f"Error on create or update person got data: {person}")
                raise HTTPException(status_code=409, detail="Person creation fail")

        @router.get(
            "/id/{item_id}",
            response_model=PersonSchema,
        )
        async def get_person_by_id_endpoint(
            person_service: PersonService,
            item_id: int,
        ):
            self.logger.debug(f"Get person by id: {item_id}")
            person = await person_service.get_by_id(item_id)
            if person is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Person id {item_id} not found",
                )
            return PersonSchema.model_validate(person)

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PersonSchema,
        )
        async def get_person_by_eesl_id_endpoint(
            person_service: PersonService,
            eesl_id: int,
        ):
            self.logger.debug(f"Get person by eesl_id: {eesl_id}")
            person = await person_service.get_person_by_eesl_id(value=eesl_id)
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
            person_service: PersonService,
            item_id: int,
            item: PersonSchemaUpdate,
        ):
            self.logger.debug(f"Update person endpoint got data: {item}")
            try:
                update_ = await person_service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(status_code=404, detail=f"Person id {item_id} not found")
                return PersonSchema.model_validate(update_)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error updating person with id:{item_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error updating person",
                ) from ex

        @router.post("/upload_photo", response_model=UploadPersonPhotoResponse)
        async def upload_person_photo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug("Upload person photo got data")
                file_location = await file_service.save_upload_image(
                    file, sub_folder="persons/photos"
                )
                return {"photoUrl": file_location}
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(f"Error on upload person photo got data: {ex}", exc_info=ex)
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading person photo",
                ) from ex

        @router.post("/upload_resize_photo", response_model=UploadResizePersonPhotoResponse)
        async def upload_and_resize_person_photo_endpoint(file: UploadFile = File(...)):
            try:
                self.logger.debug("Upload and resize person photo")
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
                self.logger.error(f"Error on upload and resize photo: {ex}", exc_info=ex)
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading and resizing person photo",
                ) from ex

        @router.get(
            "/paginated",
            response_model=PaginatedPersonResponse,
        )
        async def get_all_persons_paginated_endpoint(
            person_service: PersonService,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("second_name", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for full-text search"),
            owner_user_id: int | None = Query(None, description="Filter by owner_user_id"),
            isprivate: bool | None = Query(None, description="Filter by isprivate status"),
        ):
            self.logger.debug(
                f"Get all persons paginated: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}, "
                f"owner_user_id={owner_user_id}, isprivate={isprivate}"
            )
            skip = (page - 1) * items_per_page
            response = await person_service.search_persons_with_pagination(
                search_query=search,
                owner_user_id=owner_user_id,
                isprivate=isprivate,
                skip=skip,
                limit=items_per_page,
                order_by=order_by,
                order_by_two=order_by_two,
                ascending=ascending,
            )
            return response

        @router.get(
            "/count",
            response_model=dict[str, int],
        )
        async def get_persons_count_endpoint(person_service: PersonService) -> dict[str, int]:
            self.logger.debug("Get persons count endpoint")
            count = await person_service.get_persons_count()
            return {"total_items": count}

        @router.get(
            "/not-in-sport/{sport_id}/all",
            response_model=list[PersonSchema],
        )
        async def get_all_persons_not_in_sport_endpoint(
            person_service: PersonService,
            sport_id: int,
        ):
            self.logger.debug(f"Get all persons not in sport {sport_id}")
            persons = await person_service.get_all_persons_not_in_sport(sport_id=sport_id)
            return [PersonSchema.model_validate(p) for p in persons]

        @router.get(
            "/not-in-sport/{sport_id}",
            response_model=PaginatedPersonResponse,
        )
        async def get_persons_not_in_sport_endpoint(
            person_service: PersonService,
            sport_id: int,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("second_name", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for full-text search"),
        ):
            self.logger.debug(
                f"Get persons not in sport {sport_id}: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
            )
            skip = (page - 1) * items_per_page
            response = await person_service.get_persons_not_in_sport(
                sport_id=sport_id,
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
            summary="Delete person",
            description="Delete a person by ID. Requires admin role.",
            responses={
                200: {"description": "Person deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Person not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_person_endpoint(
            person_service: PersonService,
            model_id: int,
            _: Annotated[PersonDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete person endpoint id:{model_id}")
            await person_service.delete(model_id)
            return {"detail": f"Person {model_id} deleted successfully"}

        return router


api_person_router = PersonAPIRouter().route()
