from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SportServiceDB
from .schemas import SportSchemaCreate, SportSchema, SportSchemaUpdate


class SportAPIRouter(
    BaseRouter[
        SportSchema,
        SportSchemaCreate,
        SportSchemaUpdate,
    ]
):
    def __init__(self, service: SportServiceDB):
        super().__init__(
            "/api/sports",
            ["sports"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SportSchema,
        )
        async def create_sport_endpoint(item: SportSchemaCreate):
            new_ = await self.service.create_sport(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=SportSchema,
        )
        async def update_sport_endpoint(
                item_id: int,
                item: SportSchemaUpdate,
        ):
            update_ = await self.service.update_sport(
                item_id,
                item,
            )
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sport id:{item_id} not found",
                )
            return update_.__dict__

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sport_by_id_endpoint(
                item_id,
                item=Depends(self.service.get_by_id),
        ):
            if item:
                return self.create_response(
                    item,
                    f"Sport ID:{item.id}",
                    "Sport",
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sport id:{item_id} not found",
                )

        @router.get("/id/{sport_id}/tournaments")
        async def tournaments_by_sport_endpoint(sport_id: int):
            return await self.service.get_tournaments_by_sport(sport_id)

        @router.get("/id/{sport_id}/teams")
        async def teams_by_sport_endpoint(sport_id: int):
            return await self.service.get_teams_by_sport(sport_id)

        @router.get("/id/{sport_id}/players")
        async def players_by_sport_endpoint(sport_id: int):
            return await self.service.get_players_by_sport(sport_id)

        @router.get("/id/{sport_id}/positions")
        async def positions_by_sport_endpoint(sport_id: int):
            return await self.service.get_positions_by_sport(sport_id)

        return router


api_sport_router = SportAPIRouter(SportServiceDB(db)).route()
