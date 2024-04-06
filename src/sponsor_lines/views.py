from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SponsorLineServiceDB
from .schemas import SponsorLineSchemaCreate, SponsorLineSchema, SponsorLineSchemaUpdate


class SponsorLineAPIRouter(
    BaseRouter[
        SponsorLineSchema,
        SponsorLineSchemaCreate,
        SponsorLineSchemaUpdate,
    ]
):
    def __init__(self, service: SponsorLineServiceDB):
        super().__init__(
            "/api/sponsor_lines",
            ["sponsor_lines"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SponsorLineSchema,
        )
        async def create_sponsor_line_endpoint(item: SponsorLineSchemaCreate):
            new_ = await self.service.create_sponsor_line(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=SponsorLineSchema,
        )
        async def update_sponsor_line_endpoint(
                item_id: int,
                item: SponsorLineSchemaUpdate,
        ):
            update_ = await self.service.update_sponsor_line(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"SponsorLine id:{item_id} not found",
                )
            return update_.__dict__

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sponsor_line_by_id_endpoint(
                item_id,
                item=Depends(self.service.get_by_id),
        ):
            if item:
                return self.create_response(
                    item,
                    f"SponsorLine ID:{item.id}",
                    "SponsorLine",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"SponsorLine id:{item_id} not found",
                )

        return router


api_sponsor_line_router = SponsorLineAPIRouter(SponsorLineServiceDB(db)).route()
