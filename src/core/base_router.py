# from src.async_db.base import DATABASE_URL, Database


from typing import List, TypeVar, Generic
from fastapi import APIRouter, HTTPException

# db = Database(DATABASE_URL)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, prefix: str, tags: list[str], service):
        self.prefix = prefix
        self.service = service
        self.tags = tags

    def route(self):
        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.get("/order_by={order_by}/des={des}", response_model=List[ModelType])
        async def get_all(skip: int = 0, limit: int = 100,
                          order_by: str = 'id', des: bool = False):
            return await self.service.get_all(skip, limit, order_by, des)

        @router.get("/id/{model_id}", response_model=ModelType)
        async def get_by_id(model_id: int):
            model = await self.service.get_by_id(model_id)
            if model is None:
                raise HTTPException(status_code=404,
                                    detail=f"{ModelType.__name__} {model_id} not found")
            return model

        @router.delete("/id/{model_id}")
        async def delete(model_id: int):
            await self.service.delete(model_id)
            return {"message": f"{ModelType.__name__} {model_id} deleted"}

        return router
