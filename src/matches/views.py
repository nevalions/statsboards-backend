from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import MatchServiceDB
from .shemas import MatchSchemaCreate, MatchSchemaUpdate, MatchSchema


# Match backend
class MatchRouter(
    BaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=MatchSchema,
        )
        async def create_match(
                match: MatchSchemaCreate,
        ):
            new_match = await self.service.create_or_update_match(match)
            return new_match.__dict__

        @router.put(
            "/",
            response_model=MatchSchema,
        )
        async def update_match(
                item_id: int,
                item: MatchSchemaUpdate,
        ):
            match_update = await self.service.update_match(item_id, item)

            if match_update is None:
                raise HTTPException(
                    status_code=404, detail=f"Match id({item_id}) " f"not found"
                )
            return match_update.__dict__

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=MatchSchema,
        )
        async def get_match_by_eesl_id(eesl_id: int):
            match = await self.service.get_match_by_eesl_id(value=eesl_id)
            if match is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match eesl_id({eesl_id}) " f"not found",
                )
            return match.__dict__

        return router


api_match_router = MatchRouter(MatchServiceDB(db)).route()
