from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerMatchServiceDB
from .schemas import PlayerMatchSchema, PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from ..player.schemas import PlayerSchema
from ..player_team_tournament.schemas import PlayerTeamTournamentSchema


# Person backend
class PlayerMatchAPIRouter(
    BaseRouter[PlayerMatchSchema, PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate,]
):
    def __init__(self, service: PlayerMatchServiceDB):
        super().__init__("/api/players_match", ["players_match"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerMatchSchema,
        )
        async def create_player_match_endpoint(
                player_match: PlayerMatchSchemaCreate,
        ):
            print(f"Received player_match: {player_match}")
            new_player_match = await self.service.create_or_update_player_match(
                player_match)
            if new_player_match:
                return new_player_match.__dict__
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Person creation fail"
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerMatchSchema,
        )
        async def get_player_match_by_eesl_id_endpoint(
                player_match_eesl_id: int,
        ):
            tournament = await self.service.get_player_match_by_eesl_id(value=player_match_eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({player_match_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PlayerMatchSchema,
        )
        async def update_player_match_endpoint(
                item_id: int,
                item: PlayerMatchSchemaUpdate,
        ):
            update_ = await self.service.update_player_match(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Player team tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.get(
            "/id/{player_id}/player_in_sport/",
            response_model=PlayerSchema,
        )
        async def get_player_in_sport_endpoint(player_id: int):
            return await self.service.get_player_in_sport(player_id)

        @router.get(
            "/id/{player_id}/player_in_team_tournament/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_team_tournament_endpoint(player_id: int):
            return await self.service.get_player_in_team_tournament(player_id)

        @router.get(
            "/id/{player_id}/full_data/",
            # response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_match_full_data_endpoint(player_id: int):
            return await self.service.get_player_in_match_full_data(player_id)

        return router


api_player_match_router = PlayerMatchAPIRouter(PlayerMatchServiceDB(db)).route()
