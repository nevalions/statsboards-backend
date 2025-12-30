from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import SponsorSponsorLineServiceDB
from .schemas import (
    SponsorSponsorLineSchema,
    SponsorSponsorLineSchemaCreate,
    SponsorSponsorLineSchemaUpdate,
)
from ..logging_config import setup_logging, get_logger

setup_logging()


class SponsorSponsorLineAPIRouter(
    BaseRouter[
        SponsorSponsorLineSchema,
        SponsorSponsorLineSchemaCreate,
        SponsorSponsorLineSchemaUpdate,
    ]
):
    def __init__(self, service: SponsorSponsorLineServiceDB):
        super().__init__(
            "/api/sponsor_in_sponsor_line", ["sponsor_sponsor_line"], service
        )
        self.logger = get_logger("backend_logger_SponsorSponsorLineAPIRouter", self)
        self.logger.debug(f"Initialized SponsorSponsorLineAPIRouter")

    def route(self):
        router = super().route()

        @router.post("/{sponsor_id}in{sponsor_line_id}")
        async def create_sponsor_sponsor_line_relation_endpoint(
            sponsor_line_id: int,
            sponsor_id: int,
        ):
            try:
                self.logger.debug(f"Creating sponsor sponsor line relation endpoint")
                sponsor_sponsor_line_schema_create = SponsorSponsorLineSchemaCreate(
                    sponsor_line_id=sponsor_line_id,
                    sponsor_id=sponsor_id,
                )
                new_ = await self.service.create(sponsor_sponsor_line_schema_create)
                if new_:
                    return new_
                else:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Relation sponsor id({sponsor_id}) "
                        f"Sponsor Line id({sponsor_line_id}) "
                        f"not created. Maybe already exist.",
                    )
            except Exception as e:
                self.logger.error(
                    f"Error creating sponsor sponsor line relation endpoint: {e}",
                    exc_info=True,
                )

        @router.put(
            "/",
            response_model=SponsorSponsorLineSchema,
        )
        async def update_sponsor_sponsor_line_endpoint(
            item_id: int,
            item: SponsorSponsorLineSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Updating sponsor sponsor line endpoint")
                update_ = await self.service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Team Tournament id {item_id} not found",
                    )
                return SponsorSponsorLineSchema.model_validate(update_)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error updating sponsor sponsor line endpoint: {e}", exc_info=True
                )
                raise HTTPException(
                    status_code=409,
                    detail="Error updating sponsor sponsor line relation",
                )

        @router.get("/{sponsor_id}in{sponsor_line_id}")
        async def get_sponsor_sponsor_line_relation_endpoint(
            sponsor_id: int, sponsor_line_id: int
        ):
            try:
                self.logger.debug(f"Getting sponsor sponsor line relation endpoint")
                sponsor_sponsor_line = (
                    await self.service.get_sponsor_sponsor_line_relation(
                        sponsor_id, sponsor_line_id
                    )
                )
                if not sponsor_sponsor_line:
                    raise HTTPException(
                        status_code=404, detail="sponsor_sponsor_line not found"
                    )
                return sponsor_sponsor_line
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error getting sponsor sponsor line endpoint: {e}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error retrieving sponsor sponsor line relation",
                )

        @router.get("/sponsor_line/id/{sponsor_line_id}/sponsors")
        async def get_sponsors_in_sponsor_line_endpoint(sponsor_line_id: int):
            try:
                self.logger.debug(
                    f"Getting sponsor from sponsor line id: {sponsor_line_id} endpoint"
                )
                sponsors = await self.service.get_related_sponsors(sponsor_line_id)
                return sponsors
            except Exception as e:
                self.logger.error(
                    f"Error getting sponsor from sponsor line id:{sponsor_line_id} endpoint: {e}",
                    exc_info=True,
                )

        @router.delete("/{sponsor_id}in{sponsor_line_id}")
        async def delete_relation_by_sponsor_id_sponsor_line_id_endpoint(
            sponsor_id: int, sponsor_line_id: int
        ):
            try:
                self.logger.debug(f"Deleting sponsor sponsor line relation endpoint")
                await self.service.delete_relation_by_sponsor_and_sponsor_line_id(
                    sponsor_id, sponsor_line_id
                )
            except Exception as e:
                self.logger.error(
                    f"Error deleting relation sponsor line id: {sponsor_line_id} sponsor id: {sponsor_id} endpoint: {e}",
                    exc_info=True,
                )

        return router


api_sponsor_sponsor_line_router = SponsorSponsorLineAPIRouter(
    SponsorSponsorLineServiceDB(db)
).route()
