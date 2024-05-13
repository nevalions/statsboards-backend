from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerServiceDB
from .schemas import PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate
from ..pars_eesl.pars_all_players_from_eesl import parse_all_players_from_eesl_index_page_eesl
from ..person.db_services import PersonServiceDB
from ..person.schemas import PersonSchemaCreate


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

        @router.get(
            "/pars/all_eesl",
        )
        async def get_parse_player_with_person_teams_endpoint():
            return await parse_all_players_from_eesl_index_page_eesl(limit=2)

        @router.post("/pars_and_create/all_eesl/")
        async def create_parsed_players_with_person_endpoint():
            players = await parse_all_players_from_eesl_index_page_eesl(start_page=None, limit=None)
            created_persons = []
            created_players = []

            if players:
                for player_with_person in players:
                    person = PersonSchemaCreate(**player_with_person["person"])
                    created_person = await PersonServiceDB(db).create_or_update_person(person)
                    created_persons.append(created_person)
                    if created_person:
                        player_data_dict = player_with_person["player"]
                        player_data_dict["person_id"] = created_person.id
                        player = PlayerSchemaCreate(**player_data_dict)
                        created_player = await self.service.create_or_update_player(player)
                        created_players.append(created_player)
                return created_players, created_persons
            else:
                return []

        return router


api_player_router = PlayerAPIRouter(PlayerServiceDB(db)).route()
