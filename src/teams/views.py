from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import TeamServiceDB
from .schemas import TeamSchema, TeamSchemaCreate, TeamSchemaUpdate
from ..team_tournament.db_services import TeamTournamentServiceDB
from ..team_tournament.schemas import TeamTournamentSchemaCreate


# Team backend
class TeamAPIRouter(BaseRouter[TeamSchema, TeamSchemaCreate, TeamSchemaUpdate]):
    def __init__(self, service: TeamServiceDB):
        super().__init__("/api/teams", ["teams"], service)

    def route(self):
        router = super().route()

        @router.post("/", response_model=TeamSchema)
        async def create_team(team: TeamSchemaCreate, tour_id: int = None):
            new_team = await self.service.create_or_update_team(team)
            if new_team and tour_id:
                dict_conv = TeamTournamentSchemaCreate(
                    **{"team_id": new_team.id, "tournament_id": tour_id}
                )
                try:
                    await TeamTournamentServiceDB(db).create_team_tournament_relation(
                        tournament_id=dict_conv.tournament_id,
                        team_id=dict_conv.team_id,
                    )
                except Exception as ex:
                    print(ex)
            return new_team.__dict__

        @router.get("/eesl_id/{eesl_id}", response_model=TeamSchema)
        async def get_team_by_eesl_id(
            team_eesl_id: int,
        ):
            tournament = await self.service.get_team_by_eesl_id(value=team_eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({team_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/",
            response_model=TeamSchema,
        )
        async def update_team(
            item_id: int,
            item: TeamSchemaUpdate,
        ):
            update_ = await self.service.update_team(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Team id {item_id} not found"
                )
            return update_.__dict__

        @router.get("/id/{team_id}/matches/")
        async def get_matches_by_team(team_id: int):
            return await self.service.get_matches_by_team_id(team_id)

        return router


api_team_router = TeamAPIRouter(TeamServiceDB(db)).route()
