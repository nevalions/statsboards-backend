from typing import Any, Generic, TypeVar
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from .response_schemas import ResponseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseType = Literal["text", "json", "object"]


class MinimalBaseRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, prefix: str, tags: list[str], service):
        self.prefix = prefix
        self.service = service
        self.tags = tags

    @staticmethod
    def create_response(item: object | None, message: str, _type: ResponseType = "text") -> dict[str, object]:
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
        model_name = self.service.model.__name__.lower()

        @router.get("/", operation_id=f"get_all_{model_name}")
        async def get_all_elem():
            return await self.service.get_all_elements()

        @router.get("/id/{model_id}", operation_id=f"get_{model_name}_by_id")
        async def get_by_id(model_id: int):
            model = await self.service.get_by_id(model_id)
            if model is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{self.service.model.__name__} {model_id} not found",
                )
            return model

        @router.delete("/id/{model_id}", operation_id=f"delete_{model_name}")
        async def delete(model_id: int):
            return await self.service.delete(model_id)

        return router
