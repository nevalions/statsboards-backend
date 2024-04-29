from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerServiceDB
from .schemas import PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate


# Player backend
class PlayerAPIRouter(BaseRouter[PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate]):
    def __init__(self, service: PlayerServiceDB):
        super().__init__("/api/players", ["players"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerSchema,
        )
        async def create_player_endpoint(
                player: PlayerSchemaCreate,
        ):
            print(f"Received player: {player}")
            new_player = await self.service.create_or_update_player(player)
            if new_player:
                return new_player.__dict__
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Player creation fail"
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerSchema,
        )
        async def get_player_by_eesl_id_endpoint(
                player_eesl_id: int,
        ):
            tournament = await self.service.get_player_by_eesl_id(value=player_eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({player_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PlayerSchema,
        )
        async def update_player_endpoint(
                item_id: int,
                item: PlayerSchemaUpdate,
        ):
            update_ = await self.service.update_player(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Player id {item_id} not found"
                )
            return update_.__dict__

        @router.get("/id/{player_id}/person")
        async def person_by_player_id(player_id: int):
            return await self.service.get_player_with_person(player_id)

        return router


api_player_router = PlayerAPIRouter(PlayerServiceDB(db)).route()
