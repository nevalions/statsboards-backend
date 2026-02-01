from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from .response_schemas import ResponseModel

if TYPE_CHECKING:
    from src.core.models import BaseServiceDB

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseType = Literal["text", "json", "object"]


class MinimalBaseRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, prefix: str, tags: list[str], service, service_name: str | None = None):
        self.prefix = prefix
        self.service = service
        self.tags = tags
        self._service_name = service_name
        self._lazy_service: "BaseServiceDB | None" = None

    @property
    def loaded_service(self) -> "BaseServiceDB | None":
        """Get service instance, lazily loading from registry if not set."""
        if self.service is not None:
            return self.service
        if self._lazy_service is not None:
            return self._lazy_service
        if self._service_name is not None:
            from .service_registry import get_service_registry

            registry = get_service_registry()
            self._lazy_service = registry.get(self._service_name)
            return self._lazy_service
        return None

    @staticmethod
    def create_response(
        item: object | None, message: str, _type: ResponseType = "text"
    ) -> dict[str, object]:
        if item:
            return {
                "content": item.__dict__,
                "type": _type,
                "message": message,
                "status_code": status.HTTP_200_OK,
                "success": True,
            }

        raise HTTPException(
            status_code=404,
            detail=f"'{message}' ELEMENT NOT FOUND",
        )

    @staticmethod
    def create_pydantic_response(
        item: BaseModel | None, message: str, _type: ResponseType = "text"
    ) -> ResponseModel[BaseModel]:
        if item:
            return ResponseModel.success_response(item, message)

        raise HTTPException(
            status_code=404,
            detail=f"'{message}' ELEMENT NOT FOUND",
        )

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)
        return router


class BaseRouter(MinimalBaseRouter[ModelType, CreateSchemaType, UpdateSchemaType]):
    def route(self):
        router = super().route()

        service = self.loaded_service
        if service is None:
            return router

        model_name = service.model.__name__.lower()

        @router.get("/", operation_id=f"get_all_{model_name}")
        async def get_all_elem():
            return await service.get_all_elements()

        @router.get("/id/{model_id}", operation_id=f"get_{model_name}_by_id")
        async def get_by_id(model_id: int):
            model = await service.get_by_id(model_id)
            if model is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{service.model.__name__} {model_id} not found",
                )
            return model

        return router
