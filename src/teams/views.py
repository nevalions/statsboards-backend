from typing import List

from fastapi import HTTPException, UploadFile, File

from src.core import BaseRouter, db
from .db_services import TeamServiceDB
from .schemas import (
    TeamSchema,
    TeamSchemaCreate,
    TeamSchemaUpdate,
    UploadTeamLogoResponse,
    UploadResizeTeamLogoResponse,
)
from ..core.config import uploads_path
from ..helpers.file_service import file_service
from ..logging_config import setup_logging, get_logger
from ..pars_eesl.pars_tournament import (
    parse_tournament_teams_index_page_eesl,
    ParsedTeamData,
)

from ..team_tournament.db_services import TeamTournamentServiceDB
from ..team_tournament.schemas import TeamTournamentSchemaCreate
from ..tournaments.db_services import TournamentServiceDB

setup_logging()


# Team backend
class TeamAPIRouter(BaseRouter[TeamSchema, TeamSchemaCreate, TeamSchemaUpdate]):
    def __init__(self, service: TeamServiceDB):
        super().__init__("/api/teams", ["teams"], service)
        self.logger = get_logger("backend_logger_TeamAPIRouter", self)
        self.logger.debug(f"Initialized TeamAPIRouter")

    def route(self):
        router = super().route()

        @router.post("/", response_model=TeamSchema)
        async def create_team_endpoint(
            team: TeamSchemaCreate,
            tour_id: int | None = None,
        ):
            self.logger.debug(f"Create team endpoint got data: {team}")
            new_team = await self.service.create_or_update_team(team)
            if not new_team:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error creating new team",
                )
            if tour_id:
                self.logger.debug(f"Check if team in tournament exists")
                dict_conv = TeamTournamentSchemaCreate(
                    **{"team_id": new_team.id, "tournament_id": tour_id}
                )
                try:
                    self.logger.debug(
                        f"Try creating team_tournament connection team_id: {new_team.id} to tour_id: {tour_id}"
                    )
                    await TeamTournamentServiceDB(db).create(
                        dict_conv
                    )
                except HTTPException:
                    raise
                except Exception as ex:
                    self.logger.error(
                        f"Error creating team_tournament connection "
                        f"team_id: {new_team.id} and tour_id: {tour_id} : {ex}",
                        exc_info=True,
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error creating team tournament connection",
                    )
            return TeamSchema.model_validate(new_team)

        @router.get("/eesl_id/{eesl_id}", response_model=TeamSchema)
        async def get_team_by_eesl_id_endpoint(
            eesl_id: int,
        ):
            self.logger.debug(f"Get team by eesl_id endpoint got eesl_id:{eesl_id}")
            team = await self.service.get_team_by_eesl_id(value=eesl_id)
            if team is None:
                self.logger.warning(f"No team found with eesl_id: {eesl_id}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({eesl_id}) " f"not found",
                )
            return TeamSchema.model_validate(team)

        @router.put(
            "/{item_id}/",
            response_model=TeamSchema,
        )
        async def update_team_endpoint(
            item_id: int,
            item: TeamSchemaUpdate,
        ):
            self.logger.debug(f"Update team endpoint id:{item_id} data: {item}")
            update_ = await self.service.update(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404, detail=f"Team id {item_id} not found"
                )
            return TeamSchema.model_validate(update_)

        @router.get("/id/{team_id}/matches/")
        async def get_matches_by_team_endpoint(team_id: int):
            self.logger.debug(f"Get matches by team id:{team_id} endpoint")
            try:
                return await self.service.get_matches_by_team_id(team_id)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting matches by team id:{team_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching matches for team",
                )

        @router.get("/id/{team_id}/tournament/id/{tournament_id}/players/")
        async def get_players_by_team_and_tournament_endpoint(
            team_id: int, tournament_id: int
        ):
            self.logger.debug(
                f"Get players by team id:{team_id} and tournament id: {tournament_id} endpoint"
            )
            try:
                return await self.service.get_players_by_team_id_tournament_id(
                    team_id, tournament_id
                )
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting players by team id:{team_id} and tournament id:{tournament_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching players for team and tournament",
                )

        @router.get("/id/{team_id}/tournament/id/{tournament_id}/players_with_persons/")
        async def get_players_by_team_id_tournament_id_with_person_endpoint(
            team_id: int, tournament_id: int
        ):
            self.logger.debug(
                f"Get players with persons by team id:{team_id} and tournament id: {tournament_id} endpoint"
            )
            try:
                return await self.service.get_players_by_team_id_tournament_id_with_person(
                    team_id, tournament_id
                )
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting players with persons by team id:{team_id} and tournament id:{tournament_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching players with persons for team and tournament",
                )

        @router.post("/upload_logo", response_model=UploadTeamLogoResponse)
        async def upload_team_logo_endpoint(file: UploadFile = File(...)):
            try:
                file_location = await file_service.save_upload_image(
                    file, sub_folder="teams/logos"
                )
                self.logger.debug(
                    f"Upload team logo endpoint file location: {file_location}"
                )
                return {"logoUrl": file_location}
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(f"Error saving team logo file: {ex}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading team logo",
                )

        @router.post("/upload_resize_logo", response_model=UploadResizeTeamLogoResponse)
        async def upload_and_resize_team_logo_endpoint(file: UploadFile = File(...)):
            try:
                uploaded_paths = await file_service.save_and_resize_upload_image(
                    file,
                    sub_folder="teams/logos",
                    icon_height=100,
                    web_view_height=400,
                )
                self.logger.debug(
                    f"Upload and resize team logo endpoint file location: {uploaded_paths}"
                )
                return uploaded_paths
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error saving and resizing team logo file: {ex}", exc_info=True
                )
                raise HTTPException(
                    status_code=500,
                    detail="Error uploading and resizing team logo",
                )

        @router.get(
            "/pars/tournament/{eesl_tournament_id}",
            response_model=List[TeamSchemaCreate],
        )
        async def get_parse_tournament_teams_endpoint(eesl_tournament_id: int):
            self.logger.debug(
                f"Get parsed teams from tournament eesl_id:{eesl_tournament_id} endpoint"
            )
            return await parse_tournament_teams_index_page_eesl(eesl_tournament_id)

        @router.post("/pars_and_create/tournament/{eesl_tournament_id}")
        async def create_parsed_teams_endpoint(
            eesl_tournament_id: int,
        ):
            self.logger.debug(
                f"Get and Save parsed teams from tournament eesl_id:{eesl_tournament_id} endpoint"
            )
            tournament = await TournamentServiceDB(db).get_tournament_by_eesl_id(
                eesl_tournament_id
            )
            self.logger.debug(f"Tournament: {tournament}")
            try:
                teams_list = await parse_tournament_teams_index_page_eesl(
                    eesl_tournament_id
                )
                self.logger.debug(f"Teams after parse: {teams_list}")

                created_teams = []
                created_team_tournament_ids = []
                try:
                    if teams_list:
                        for t in teams_list:
                            t: ParsedTeamData
                            team = TeamSchemaCreate(**t)
                            created_team = await self.service.create_or_update_team(
                                team
                            )
                            self.logger.debug(
                                f"Created or updated team after parse {created_team}"
                            )
                            created_teams.append(created_team)
                            if created_team and tournament:
                                dict_conv = TeamTournamentSchemaCreate(
                                    **{
                                        "team_id": created_team.id,
                                        "tournament_id": tournament.id,
                                    }
                                )
                                try:
                                    self.logger.debug(
                                        f"Trying to create team and tournament connection after parse"
                                    )
                                    team_tournament_connection = (
                                        await TeamTournamentServiceDB(
                                            db
                                        ).create(dict_conv)
                                    )
                                    created_team_tournament_ids.append(
                                        team_tournament_connection
                                    )
                                except Exception as ex:
                                    self.logger.error(
                                        f"Error create team and tournament connection after parse {ex}",
                                        exc_info=True,
                                    )
                        self.logger.info(
                            f"Created teams after parsing: {created_teams}"
                        )
                        self.logger.info(
                            f"Created team tournament connections after parsing: {created_team_tournament_ids}"
                        )

                        return created_teams, created_team_tournament_ids
                    else:
                        self.logger.warning(f"Team list is empty")
                        return []
                except HTTPException:
                    raise
                except Exception as ex:
                    self.logger.error(
                        f"Error on parse and create teams from tournament: {ex}",
                        exc_info=True,
                    )
                    raise HTTPException(
                        status_code=500,
                        detail="Internal server error parsing and creating teams from tournament",
                    )
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error on parse and create teams from tournament: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error parsing and creating teams from tournament",
                )

        return router


api_team_router = TeamAPIRouter(TeamServiceDB(db)).route()
