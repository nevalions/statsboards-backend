from typing import List
from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_service import TournamentServiceDB
from .schemas import TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate


# Tournament backend
class TournamentRouter(BaseRouter[TournamentSchema, TournamentSchemaCreate,
TournamentSchemaUpdate]):

    def __init__(self, service: TournamentServiceDB):
        super().__init__("/api/tournaments", ["tournaments"], service)

    def route(self):
        router = super().route()

        @router.post("/", response_model=TournamentSchema)
        async def create_tournament(item: TournamentSchemaCreate):
            new_ = await self.service.create_tournament(item)
            return new_.__dict__

        @router.put("/", response_model=TournamentSchema)
        async def update_tournament(
                item_id: int,
                item: TournamentSchemaUpdate
        ):
            update_ = await self.service.update_tournament(item_id, item)
            if update_ is None:
                raise HTTPException(status_code=404,
                                    detail=f"Tournament id {item_id} not found")
            return update_.__dict__

        @router.get("/eesl_id/{eesl_id}", response_model=TournamentSchema)
        async def get_tournament_by_eesl_id(
                tournament_eesl_id: int,
        ):
            tournament = await self.service.get_tournament_by_eesl_id(
                value=tournament_eesl_id
            )
            if tournament is None:
                raise HTTPException(status_code=404,
                                    detail=f"Tournament eesl_id({tournament_eesl_id}) "
                                           f"not found")
            return tournament.__dict__

        @router.get("/year/{year}/order_by={order_by}/des={des}",
                    response_model=List[TournamentSchema])
        async def get_tournaments_by_year(
                year: int,
                order_by: str = 'fk_season',
                descending: bool = False,
                skip: int = 0, limit: int = 100
        ):
            return await self.service.get_tournaments_by_year(year,
                                                              order_by=order_by,
                                                              descending=descending,
                                                              skip=skip, limit=limit)

        return router


api_tournament_router = TournamentRouter(TournamentServiceDB(db)).route()
