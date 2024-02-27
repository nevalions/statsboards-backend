from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import TeamTournamentServiceDB
from .schemas import (
    TeamTournamentSchema,
    TeamTournamentSchemaCreate,
    TeamTournamentSchemaUpdate,
)
from src.teams.schemas import TeamSchema


# Team backend
class TeamTournamentRouter(
    BaseRouter[
        TeamTournamentSchema, TeamTournamentSchemaCreate, TeamTournamentSchemaUpdate
    ]
):
    def __init__(self, service: TeamTournamentServiceDB):
        super().__init__("/api/team_in_tournament", ["team_tournament"], service)

    def route(self):
        router = super().route()

        @router.post("/{team_id}in{tournament_id}")
        async def create_team_tournament_relation_endpoint(
                tournament_id: int,
                team_id: int,
        ):

            team_tournament_schema_create = TeamTournamentSchemaCreate(
                tournament_id=tournament_id,
                team_id=team_id,
            )
            new_ = await self.service.create_team_tournament_relation(
                team_tournament_schema_create
            )
            print(new_)
            if new_:
                return new_
            else:
                raise HTTPException(
                    status_code=409,
                    detail=f"Relation Team id({team_id}) "
                           f"Tournament id({tournament_id}) "
                           f"not created. Maybe already exist.",
                )

        @router.put(
            "/",
            response_model=TeamTournamentSchema,
        )
        async def update_tournament_endpoint(
                item_id: int,
                item: TeamTournamentSchemaUpdate,
        ):
            update_ = await self.service.update_team_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Team Tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.get("/{team_id}in{tournament_id}")
        async def get_team_tournament_relation_endpoint(team_id: int, tournament_id: int):
            team_tournament = await self.service.get_team_tournament_relation(team_id, tournament_id)
            if not team_tournament:
                raise HTTPException(status_code=404, detail="Team Tournament not found")
            return team_tournament

        @router.get("/tournament/id/{tournament_id}/teams")
        async def get_teams_in_tournament_endpoint(tournament_id: int):
            teams = await self.service.get_related_teams(tournament_id)
            return teams

        @router.delete("/{team_id}in{tournament_id}")
        async def delete_relation_by_team_id_tournament_id_endpoint(team_id: int, tournament_id: int):
            await self.service.delete_relation_by_team_and_tournament_id(team_id, tournament_id)

        return router


api_team_tournament_router = TeamTournamentRouter(TeamTournamentServiceDB(db)).route()
