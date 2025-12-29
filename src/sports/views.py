from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from .db_services import SportServiceDB
from .schemas import SportSchemaCreate, SportSchema, SportSchemaUpdate
from ..logging_config import setup_logging, get_logger

setup_logging()


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
        self.logger = get_logger("backend_logger_SportAPIRouter", self)
        self.logger.debug(f"Initialized SportAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=SportSchema,
        )
        async def create_sport_endpoint(item: SportSchemaCreate):
            self.logger.debug(f"Create sport endpoint got data: {item}")
            new_ = await self.service.create(item)
            return SportSchema.model_validate(new_)

        @router.put(
            "/",
            response_model=SportSchema,
        )
        async def update_sport_endpoint(
            item_id: int,
            item: SportSchemaUpdate,
        ):
            self.logger.debug(f"Update sport endpoint id:{item_id} data: {item}")
            update_ = await self.service.update(
                item_id,
                item,
            )
            return SportSchema.model_validate(update_)

        @router.get(
            "/id/{item_id}/",
            response_class=JSONResponse,
        )
        async def get_sport_by_id_endpoint(item_id: int):
            self.logger.debug(f"Getting sport by id: {item_id} endpoint")
            item = await self.service.get_by_id(item_id)
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
            self.logger.debug(f"Get tournaments by sport id:{sport_id} endpoint")
            return await self.service.get_tournaments_by_sport(sport_id)

        @router.get("/id/{sport_id}/teams")
        async def teams_by_sport_endpoint(sport_id: int):
            self.logger.debug(f"Get teams by sport id:{sport_id} endpoint")
            return await self.service.get_teams_by_sport(sport_id)

        @router.get("/id/{sport_id}/players")
        async def players_by_sport_endpoint(sport_id: int):
            self.logger.debug(f"Get players by sport id:{sport_id} endpoint")
            return await self.service.get_players_by_sport(sport_id)

        @router.get("/id/{sport_id}/positions")
        async def positions_by_sport_endpoint(sport_id: int):
            self.logger.debug(f"Get positions by sport id:{sport_id} endpoint")
            return await self.service.get_positions_by_sport(sport_id)

        return router


api_sport_router = SportAPIRouter(SportServiceDB(db)).route()
