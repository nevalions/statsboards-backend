from typing import List, TypeVar, Generic, Optional, Any
from fastapi import APIRouter, HTTPException
from fastapi.params import Query
from starlette import status

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class MinimalBaseRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, prefix: str, tags: list[str], service):
        self.prefix = prefix
        self.service = service
        self.tags = tags

    @staticmethod
    def create_response(item: Optional[Any], message: str, _type: str = "text"):
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

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)
        return router


class BaseRouter(MinimalBaseRouter[ModelType, CreateSchemaType, UpdateSchemaType]):
    def route(self):
        router = super().route()

        @router.get("/")
        async def get_all_elem(
                skip: int = Query(0, description="Skip items"),
                limit: int = Query(500, description="Limit items"),
                order_by: str = Query("id", description="Order items by"),
                des: bool = Query(False, description="Sort items in descending order"),
        ):
            return await self.service.get_all_elements(skip, limit, order_by, des)

        @router.get("/id/{model_id}")  # Remove response_model temporarily
        async def get_by_id(model_id: int):
            model = await self.service.get_by_id(model_id)
            print(f"Content of model: {model}")  # Print the content for inspection
            if model is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{str(ModelType.__name__)} {model_id} not found",
                )
            return model

        @router.delete("/id/{model_id}")
        async def delete(model_id: int):
            await self.service.delete(model_id)
            return {"message": f"{ModelType.__name__} {model_id} deleted"}

        return router
