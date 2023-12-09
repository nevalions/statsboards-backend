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

        @router.post("/")
        async def create_team_tournament_relation(
                tournament_id: int,
                team_id: int,
        ):
            new_ = await self.service.create_team_tournament_relation(
                tournament_id,
                team_id,
            )
            print(new_)
            if new_:
                return new_
            else:
                raise HTTPException(
                    status_code=409,
                    # detail=f"Relation Team id({item.fk_team}) "
                    # f"Tournament id({item.fk_tournament}) "
                    # f"not created. Maybe already exist.",
                )

        @router.put(
            "/",
            response_model=TeamTournamentSchema,
        )
        async def update_tournament(
                item_id: int,
                item: TeamTournamentSchemaUpdate,
        ):
            update_ = await self.service.update_team_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Team Tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.delete("/relations/{rel_id}")
        async def delete_team_tournament_relation(rel_id: int):
            return await self.service.delete_team_tournament_relationship(rel_id)

        @router.get("/relations/")
        async def get_all_team_tournaments_relationships():
            return await self.service.get_all_team_tournaments_relationships_ids()

        @router.get(
            "/tournament/id/{tournament_id}/teams/",
            # response_model=List[TeamSchema]
        )
        async def get_teams_by_tournament_id(tournament_id: int):
            return await self.service.get_teams_by_tournament(tournament_id)

        return router


api_team_tournament_router = TeamTournamentRouter(TeamTournamentServiceDB(db)).route()
