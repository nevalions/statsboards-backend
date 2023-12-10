from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import TournamentServiceDB
from .schemas import TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate


# Tournament backend
class TournamentRouter(
    BaseRouter[
        TournamentSchema,
        TournamentSchemaCreate,
        TournamentSchemaUpdate,
    ]
):
    def __init__(self, service: TournamentServiceDB):
        super().__init__(
            "/api/tournaments",
            ["tournaments"],
            service,
        )

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=TournamentSchema,
        )
        async def create_tournament(item: TournamentSchemaCreate):
            new_ = await self.service.create_tournament(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=TournamentSchema,
        )
        async def update_tournament(
            item_id: int,
            item: TournamentSchemaUpdate,
        ):
            update_ = await self.service.update_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Tournament id {item_id} not found"
                )
            return update_.__dict__

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=TournamentSchema,
        )
        async def get_tournament_by_eesl_id(eesl_id: int):
            tournament = await self.service.get_tournament_by_eesl_id(value=eesl_id)
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.get(
            "/id/{tournament_id}/teams/",
            # response_model=List[TeamSchema]
        )
        async def get_teams_by_tournament_id(tournament_id: int):
            return await self.service.get_teams_by_tournament(tournament_id)

        return router


api_tournament_router = TournamentRouter(TournamentServiceDB(db)).route()
