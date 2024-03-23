from fastapi import HTTPException, UploadFile, File, Form

from src.core import BaseRouter, db
from .db_services import TeamServiceDB
from .schemas import TeamSchema, TeamSchemaCreate, TeamSchemaUpdate, UploadTeamLogoResponse
from ..core.config import uploads_path
from ..helpers.file_service import file_service

from ..team_tournament.db_services import TeamTournamentServiceDB
from ..team_tournament.schemas import TeamTournamentSchemaCreate


# Team backend
class TeamAPIRouter(BaseRouter[TeamSchema, TeamSchemaCreate, TeamSchemaUpdate]):
    def __init__(self, service: TeamServiceDB):
        super().__init__("/api/teams", ["teams"], service)

    def route(self):
        router = super().route()

        @router.post("/", response_model=TeamSchema)
        async def create_team(
                team: TeamSchemaCreate,
                tour_id: int = None,
        ):
            print(f"Received team: {team}")
            new_team = await self.service.create_or_update_team(team)
            if new_team and tour_id:
                dict_conv = TeamTournamentSchemaCreate(
                    **{"team_id": new_team.id, "tournament_id": tour_id}
                )
                try:
                    await TeamTournamentServiceDB(db).create_team_tournament_relation(
                        dict_conv
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

        @router.post("/upload_logo", response_model=UploadTeamLogoResponse)
        async def upload_team_logo(file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder='teams/logos')
            print(uploads_path)
            return {"logoUrl": file_location}

        return router


# file_service = FileService()
api_team_router = TeamAPIRouter(TeamServiceDB(db)).route()
