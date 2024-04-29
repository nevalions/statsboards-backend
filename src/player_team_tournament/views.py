from typing import List, Optional

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerTeamTournamentServiceDB
from .schemas import PlayerTeamTournamentSchema, PlayerTeamTournamentSchemaCreate, PlayerTeamTournamentSchemaUpdate
from ..person.schemas import PersonSchema


# Person backend
class PlayerTeamTournamentAPIRouter(
    BaseRouter[PlayerTeamTournamentSchema, PlayerTeamTournamentSchemaCreate, PlayerTeamTournamentSchemaUpdate,]
):
    def __init__(self, service: PlayerTeamTournamentServiceDB):
        super().__init__("/api/players_team_tournament", ["players_team_tournament"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def create_player_team_tournament_endpoint(
                player_team_tournament: PlayerTeamTournamentSchemaCreate,
        ):
            print(f"Received player_team_tournament: {player_team_tournament}")
            new_player_team_tournament = await self.service.create_or_update_player_team_tournament(
                player_team_tournament)
            if new_player_team_tournament:
                return new_player_team_tournament.__dict__
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Person creation fail"
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_team_tournament_by_eesl_id_endpoint(
                player_team_tournament_eesl_id: int,
        ):
            tournament = await self.service.get_player_team_tournament_by_eesl_id(value=player_team_tournament_eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({player_team_tournament_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def update_player_team_tournament_endpoint(
                item_id: int,
                item: PlayerTeamTournamentSchemaUpdate,
        ):
            update_ = await self.service.update_player_team_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Person id {item_id} not found"
                )
            return update_.__dict__

        @router.get(
            "/id/{player_id}/person/",
            response_model=PersonSchema,
        )
        async def get_player_team_tournament_with_person_endpoint(player_id: int):
            return await self.service.get_player_team_tournament_with_person(player_id)

        return router


api_player_team_tournament_router = PlayerTeamTournamentAPIRouter(PlayerTeamTournamentServiceDB(db)).route()
