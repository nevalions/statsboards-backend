from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import SponsorSponsorLineServiceDB
from .schemas import (
    SponsorSponsorLineSchema,
    SponsorSponsorLineSchemaCreate,
    SponsorSponsorLineSchemaUpdate,
)


# Team backend
class SponsorSponsorLineRouter(
    BaseRouter[
        SponsorSponsorLineSchema, SponsorSponsorLineSchemaCreate, SponsorSponsorLineSchemaUpdate
    ]
):
    def __init__(self, service: SponsorSponsorLineServiceDB):
        super().__init__("/api/sponsor_in_sponsor_line", ["sponsor_sponsor_line"], service)

    def route(self):
        router = super().route()

        @router.post("/{sponsor_id}in{sponsor_line_id}")
        async def create_sponsor_sponsor_line_relation_endpoint(
                sponsor_line_id: int,
                sponsor_id: int,
        ):

            sponsor_sponsor_line_schema_create = SponsorSponsorLineSchemaCreate(
                sponsor_line_id=sponsor_line_id,
                sponsor_id=sponsor_id,
            )
            new_ = await self.service.create_sponsor_sponsor_line_relation(
                sponsor_sponsor_line_schema_create
            )
            print(new_)
            if new_:
                return new_
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Relation Team id({sponsor_id}) "
                           f"Tournament id({sponsor_line_id}) "
                           f"not created. Maybe already exist.",
                )

        @router.put(
            "/",
            response_model=SponsorSponsorLineSchema,
        )
        async def update_sponsor_sponsor_line_endpoint(
                item_id: int,
                item: SponsorSponsorLineSchemaUpdate,
        ):
            update_ = await self.service.update_sponsor_sponsor_line(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Team Tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.get("/{sponsor_id}in{sponsor_line_id}")
        async def get_sponsor_sponsor_line_relation_endpoint(sponsor_id: int, sponsor_line_id: int):
            sponsor_sponsor_line = await self.service.get_sponsor_sponsor_line_relation(sponsor_id, sponsor_line_id)
            if not sponsor_sponsor_line:
                raise HTTPException(status_code=404, detail="sponsor_sponsor_line not found")
            return sponsor_sponsor_line

        @router.get("/sponsor_line/id/{sponsor_line_id}/sponsors")
        async def get_sponsors_in_sponsor_line_endpoint(sponsor_line_id: int):
            sponsors = await self.service.get_related_sponsors(sponsor_line_id)
            return sponsors

        @router.delete("/{sponsor_id}in{sponsor_line_id}")
        async def delete_relation_by_sponsor_id_sponsor_line_id_endpoint(sponsor_id: int, sponsor_line_id: int):
            await self.service.delete_relation_by_sponsor_and_sponsor_line_id(sponsor_id, sponsor_line_id)

        return router


api_sponsor_sponsor_line_router = SponsorSponsorLineRouter(SponsorSponsorLineServiceDB(db)).route()
