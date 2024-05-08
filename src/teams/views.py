from typing import List

from fastapi import HTTPException, UploadFile, File

from src.core import BaseRouter, db
from .db_services import TeamServiceDB
from .schemas import TeamSchema, TeamSchemaCreate, TeamSchemaUpdate, UploadTeamLogoResponse, \
    UploadResizeTeamLogoResponse
from ..core.config import uploads_path
from ..helpers.file_service import file_service
from ..pars_eesl.pars_tournament import parse_tournament_teams_index_page_eesl

from ..team_tournament.db_services import TeamTournamentServiceDB
from ..team_tournament.schemas import TeamTournamentSchemaCreate
from ..tournaments.db_services import TournamentServiceDB


# Team backend
class TeamAPIRouter(BaseRouter[TeamSchema, TeamSchemaCreate, TeamSchemaUpdate]):
    def __init__(self, service: TeamServiceDB):
        super().__init__("/api/teams", ["teams"], service)

    def route(self):
        router = super().route()

        @router.post("/", response_model=TeamSchema)
        async def create_team_endpoint(
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
        async def get_team_by_eesl_id_endpoint(
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
            "/{item_id}/",
            response_model=TeamSchema,
        )
        async def update_team_endpoint(
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
        async def get_matches_by_team_endpoint(team_id: int):
            return await self.service.get_matches_by_team_id(team_id)

        @router.get("/id/{team_id}/tournament/id/{tournament_id}/players/")
        async def get_players_by_team_and_tournament_endpoint(team_id: int, tournament_id: int):
            return await self.service.get_players_by_team_id_tournament_id(team_id, tournament_id)

        @router.post("/upload_logo", response_model=UploadTeamLogoResponse)
        async def upload_team_logo_endpoint(file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(file, sub_folder='teams/logos')
            print(uploads_path)
            return {"logoUrl": file_location}

        @router.post("/upload_resize_logo", response_model=UploadResizeTeamLogoResponse)
        async def upload_and_resize_team_logo_endpoint(file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder='teams/logos',
                icon_height=100,
                web_view_height=400,
            )
            # print(uploaded_paths)
            return uploaded_paths

        @router.get(
            "/pars/tournament/{eesl_tournament_id}",
            response_model=List[TeamSchemaCreate],
        )
        async def get_parse_tournament_teams_endpoint(eesl_tournament_id: int):
            return await parse_tournament_teams_index_page_eesl(eesl_tournament_id)

        @router.post("/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_teams_endpoint(
                eesl_tournament_id: int,
        ):
            tournament = await TournamentServiceDB(db).get_tournament_by_eesl_id(eesl_tournament_id)
            teams_list = await parse_tournament_teams_index_page_eesl(eesl_tournament_id)
            # print(teams_list)

            created_teams = []
            created_team_tournament_ids = []
            if teams_list:
                for t in teams_list:
                    team = TeamSchemaCreate(**t)
                    created_team = await self.service.create_or_update_team(team)
                    # print(created_team.__dict__)
                    created_teams.append(created_team)
                    if created_team and tournament:
                        dict_conv = TeamTournamentSchemaCreate(
                            **{"team_id": created_team.id, "tournament_id": tournament.id}
                        )
                        try:
                            team_tournament_connection = await TeamTournamentServiceDB(
                                db).create_team_tournament_relation(
                                dict_conv
                            )
                            created_team_tournament_ids.append(team_tournament_connection)
                        except Exception as ex:
                            print(ex)

                return created_teams, created_team_tournament_ids
            else:
                return []

        return router


api_team_router = TeamAPIRouter(TeamServiceDB(db)).route()
