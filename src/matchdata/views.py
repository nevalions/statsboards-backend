from typing import List

from fastapi import HTTPException, Depends, status
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import MatchDataServiceDB
from .schemas import MatchDataSchemaCreate, MatchDataSchemaUpdate, MatchDataSchema


class MatchDataRouter(
    BaseRouter[
        MatchDataSchema,
        MatchDataSchemaCreate,
        MatchDataSchemaUpdate,
    ]
):
    def __init__(self, service: MatchDataServiceDB):
        super().__init__(
            "/api/matchdata",
            ["matchdata"],
            service,
        )

    def route(self):
        router = super().route()

        # Match data backend
        @router.post(
            "/",
            response_model=MatchDataSchema,
        )
        async def create_match_data(match_data: MatchDataSchemaCreate):
            new_match_data = await self.service.create_match_data(match_data)
            return new_match_data.__dict__

        @router.put(
            "/{item_id}/",
            response_model=MatchDataSchema,
        )
        async def update_match_data_(
            item_id: int,
            match: MatchDataSchemaUpdate,
        ):
            match_data_update = await self.service.update_match_data(
                item_id,
                match,
            )

            if match_data_update is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match data " f"id({item_id}) " f"not found",
                )
            return match_data_update

        @router.put("/id/{item_id}/", response_class=JSONResponse)
        async def update_matchdata_by_id(
            item_id: int,
            item=Depends(update_match_data_),
        ):
            if item:
                return {
                    "content": item.__dict__,
                    "status_code": status.HTTP_200_OK,
                    "success": True,
                }

            raise HTTPException(
                status_code=404,
                detail=f"MatchData id:{item_id} not found",
            )

        return router


api_matchdata_router = MatchDataRouter(MatchDataServiceDB(db)).route()
