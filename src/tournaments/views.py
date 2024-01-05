from typing import List

from fastapi import HTTPException, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from src.core import BaseRouter, db
from src.core.config import match_template_path

from .db_services import TournamentServiceDB
from .schemas import TournamentSchema, TournamentSchemaCreate, TournamentSchemaUpdate
from ..matchdata.db_services import MatchDataServiceDB
from ..matchdata.schemas import MatchDataSchemaCreate
from ..matches.db_services import MatchServiceDB

match_templates = Jinja2Templates(directory=match_template_path)


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
        async def create_tournament_endpoint(item: TournamentSchemaCreate):
            new_ = await self.service.create_or_update_tournament(item)
            return new_.__dict__

        @router.put(
            "/",
            response_model=TournamentSchema,
        )
        async def update_tournament_endpoint(
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
        async def get_tournament_by_eesl_id_endpoint(eesl_id: int):
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
        async def get_teams_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_teams_by_tournament(tournament_id)

        @router.get(
            "/id/{tournament_id}/matches/",
            # response_model=List[TeamSchema]
        )
        async def get_matches_by_tournament_id_endpoint(tournament_id: int):
            return await self.service.get_matches_by_tournament(tournament_id)

        @router.get("/id/{tournament_id}/matches/create/")
        async def create_match_in_tournament(
            tournament_id,
            request: Request,
        ):
            return match_templates.TemplateResponse(
                "/display/create-match.html",
                {
                    "request": request,
                    "tournament_id": tournament_id,
                },
                status_code=200,
            )

        @router.get(
            "/id/{tournament_id}/matches/all/data/",
            response_class=JSONResponse,
        )
        async def all_tournament_matches_data_endpoint(
            tournament_id: int,
            all_matches: List = Depends(
                self.service.get_matches_by_tournament
            ),  # Fetch all tournament matches
        ):
            if all_matches is None:
                raise HTTPException(
                    status_code=404,
                    detail="No matches found for the tournament",
                )
            match_service_db = MatchServiceDB(db)
            match_data_service_db = MatchDataServiceDB(db)

            # print(all_matches)
            all_match_data = []
            for match in all_matches:
                if match is None:
                    raise HTTPException(
                        404,
                        "Match not found",
                    )
                match_id = match.id
                match_teams_data = await match_service_db.get_teams_by_match(match_id)
                match_data = await match_service_db.get_matchdata_by_match(match_id)

                if match_data is None:
                    match_data_schema = MatchDataSchemaCreate(
                        match_id=match_id,
                    )  # replace the arguments with real values
                    match_data = await match_data_service_db.create_match_data(
                        match_data_schema
                    )

                all_match_data.append(
                    {
                        "match_id": match_id,
                        "status_code": status.HTTP_200_OK,
                        "teams_data": match_teams_data,
                        "match_data": match_data.__dict__,
                    },
                )
            return all_match_data

        @router.get(
            "/id/{tournament_id}/matches/all/",
            response_class=JSONResponse,
        )
        async def get_all_tournament_matches_endpoint(
            tournament_id: int,
            request: Request,
        ):
            template = match_templates.TemplateResponse(
                name="/display/all-tournament-matches.html",
                context={
                    "request": request,
                    "tournament_id": tournament_id,
                },
                status_code=200,
            )
            return template

        return router


api_tournament_router = TournamentRouter(TournamentServiceDB(db)).route()
