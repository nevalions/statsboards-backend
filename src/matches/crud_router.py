from fastapi import Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.core import BaseRouter
from src.core.service_registry import get_service_registry
from src.gameclocks.schemas import GameClockSchemaCreate
from src.helpers.file_service import file_service
from src.logging_config import get_logger
from src.matchdata.schemas import MatchDataSchemaCreate
from src.playclocks.schemas import PlayClockSchemaCreate
from src.scoreboards.schemas import ScoreboardSchemaCreate, ScoreboardSchemaUpdate
from src.teams.schemas import UploadResizeTeamLogoResponse, UploadTeamLogoResponse

from .db_services import MatchServiceDB
from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
)


class MatchCRUDRouter(
    BaseRouter[
        MatchSchema,
        MatchSchemaCreate,
        MatchSchemaUpdate,
    ]
):
    def __init__(self, service: MatchServiceDB):
        super().__init__(
            "/api/matches",
            ["matches-api"],
            service,
        )
        self.logger = get_logger("backend_logger_MatchCRUDRouter", self)
        self.logger.debug("Initialized MatchCRUDRouter")
        self._service_registry = None

    @property
    def service_registry(self):
        if self._service_registry is None:
            self._service_registry = get_service_registry()
        return self._service_registry

    def get_match_stats_service(self):
        """Get match stats service using this router's database."""
        from src.matches.stats_service import MatchStatsServiceDB

        return MatchStatsServiceDB(self.service.db)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=MatchSchema,
            summary="Create a new match",
            description="Creates a new match between two teams. Returns the created match with its ID.",
            responses={
                200: {"description": "Match created successfully"},
                409: {"description": "Conflict - match creation failed"},
                400: {"description": "Bad request - validation error"},
            },
        )
        async def create_match_endpoint(
            match: MatchSchemaCreate,
        ):
            self.logger.debug(f"Create or update match endpoint got data: {match}")
            new_match = await self.service.create_or_update_match(match)
            if new_match:
                return MatchSchema.model_validate(new_match)
            else:
                self.logger.error(f"Error creating match with data: {match}")
                raise HTTPException(status_code=409, detail="Match creation fail")

        @router.post(
            "/create_with_full_data/",
            summary="Create match with full data",
            description="Creates a match and automatically creates associated match data, playclock, gameclock, and scoreboard.",
            responses={
                200: {"description": "Match created with full data successfully"},
                400: {"description": "Bad request - validation error"},
                500: {"description": "Internal server error"},
            },
        )
        async def create_match_with_full_data_endpoint(
            data: MatchSchemaCreate,
        ):
            self.logger.debug(f"Create or update match with full data endpoint got data: {data}")
            teams_service = self.service_registry.get("team")
            tournament_service = self.service_registry.get("tournament")
            sponsor_service = self.service_registry.get("sponsor")
            match_db_service = self.service_registry.get("matchdata")
            self.service_registry.get("playclock")
            self.service_registry.get("gameclock")
            scoreboard_db_service = self.service_registry.get("scoreboard")

            new_match = await self.service.create_or_update_match(data)

            default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
            PlayClockSchemaCreate(match_id=new_match.id)
            GameClockSchemaCreate(match_id=new_match.id)

            tournament = await tournament_service.get_by_id(new_match.tournament_id)
            tournament_main_sponsor = await sponsor_service.get_by_id(tournament.main_sponsor_id)
            team_a = await teams_service.get_by_id(new_match.team_a_id)
            team_b = await teams_service.get_by_id(new_match.team_b_id)

            existing_scoreboard = await scoreboard_db_service.get_scoreboard_by_match_id(
                new_match.id
            )

            scoreboard_schema: ScoreboardSchemaCreate | ScoreboardSchemaUpdate  # type: ignore[assignment]
            if existing_scoreboard is None:
                scoreboard_schema = ScoreboardSchemaCreate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=tournament_main_sponsor.scale_logo,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title,
                    team_b_game_title=team_b.title,
                )
            else:
                scoreboard_schema = ScoreboardSchemaUpdate(
                    match_id=new_match.id,
                    scale_tournament_logo=2,
                    scale_main_sponsor=tournament_main_sponsor.scale_logo,
                    scale_logo_a=2,
                    scale_logo_b=2,
                    team_a_game_color=team_a.team_color,
                    team_b_game_color=team_b.team_color,
                    team_a_game_title=team_a.title,
                    team_b_game_title=team_b.title,
                )
            new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(
                scoreboard_schema
            )

            new_match_data = await match_db_service.create(default_match_data)
            teams_data = await self.service.get_teams_by_match(new_match_data.match_id)

            return {
                "status_code": 200,
                "match": new_match,
                "match_data": new_match_data,
                "teams_data": teams_data,
                "scoreboard": new_scoreboard,
            }

        @router.put(
            "/{item_id}/",
            response_model=MatchSchema,
        )
        async def update_match_endpoint(
            item_id: int,
            item: MatchSchemaUpdate,
        ):
            self.logger.debug(f"Update match endpoint id:{item_id} data: {item}")
            try:
                match_update = await self.service.update(item_id, item)
                return MatchSchema.model_validate(match_update)
            except HTTPException:
                raise

        @router.get(
            "/eesl_id/{eesl_id}/",
            response_model=MatchSchema,
        )
        async def get_match_by_eesl_id_endpoint(eesl_id: int):
            self.logger.debug(f"Get match by eesl_id endpoint got eesl_id:{eesl_id}")
            match = await self.service.get_match_by_eesl_id(value=eesl_id)
            if match is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Match eesl_id({eesl_id}) not found",
                )
            return MatchSchema.model_validate(match)

        @router.get(
            "/id/{match_id}/sport/",
        )
        async def get_match_sport_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sport by match id:{match_id} endpoint")
            return await self.service.get_sport_by_match_id(match_id)

        @router.get(
            "/id/{match_id}/teams/",
        )
        async def get_match_teams_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sport by match id:{match_id} endpoint")
            return await self.service.get_teams_by_match(match_id)

        @router.get(
            "/id/{match_id}/home_away_teams/",
        )
        async def get_match_home_away_teams_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get match home and away teams by match id:{match_id} endpoint")
            return await self.service.get_teams_by_match_id(match_id)

        @router.get("/id/{match_id}/players/")
        async def get_players_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get players by match id:{match_id} endpoint")
            return await self.service.get_players_by_match(match_id)

        @router.get("/id/{match_id}/players_fulldata/")
        async def get_players_with_full_data_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get players with full data by match id:{match_id} endpoint")
            return await self.service.get_player_by_match_full_data(match_id)

        @router.get("/id/{match_id}/sponsor_line")
        async def get_sponsor_line_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get sponsor_line by match id:{match_id} endpoint")
            sponsor_line = await self.service.get_match_sponsor_line(match_id)
            if sponsor_line:
                sponsor_sponsor_line_service = self.service_registry.get("sponsor_sponsor_line")
                full_sponsor_line = await sponsor_sponsor_line_service.get_related_sponsors(
                    sponsor_line.id
                )
                return full_sponsor_line

        @router.get(
            "/id/{match_id}/match_data/",
        )
        async def get_match_data_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get matchdata by match id:{match_id} endpoint")
            return await self.service.get_matchdata_by_match(match_id)

        @router.get(
            "/id/{match_id}/playclock/",
        )
        async def get_playclock_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get playclock by match id:{match_id} endpoint")
            return await self.service.get_playclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/gameclock/",
        )
        async def get_gameclock_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get gameclock by match id:{match_id} endpoint")
            return await self.service.get_gameclock_by_match(match_id)

        @router.get(
            "/id/{match_id}/scoreboard_data/",
        )
        async def get_match_scoreboard_by_match_id_endpoint(match_id: int):
            self.logger.debug(f"Get scoreboard_data by match id:{match_id} endpoint")
            return await self.service.get_scoreboard_by_match(match_id)

        @router.get("/all/data/", response_class=JSONResponse)
        async def all_matches_data_endpoint_endpoint(
            all_matches: list = Depends(self.service.get_all_elements),
        ):
            from src.helpers.fetch_helpers import fetch_list_of_matches_data

            self.logger.debug("Get all match data by match endpoint")
            return await fetch_list_of_matches_data(all_matches)

        @router.get(
            "/id/{match_id}/data/",
            response_class=JSONResponse,
        )
        async def match_data_endpoint(
            match_teams_data=Depends(get_match_teams_by_match_id_endpoint),
            match_data=Depends(get_match_data_by_match_id_endpoint),
        ):
            self.logger.debug("Get teams and match data by match endpoint")
            return (
                {
                    "status_code": 200,
                    "teams_data": match_teams_data,
                    "match_data": match_data.__dict__,
                },
            )

        @router.get(
            "/id/{match_id}/scoreboard/full_data/",
            response_class=JSONResponse,
        )
        async def full_match_data_endpoint(match_id: int):
            from src.helpers.fetch_helpers import fetch_match_data

            self.logger.debug("Get full_match_data by match endpoint")
            return await fetch_match_data(match_id)

        @router.get(
            "/id/{match_id}/scoreboard/full_data/scoreboard_settings/",
            response_class=JSONResponse,
        )
        async def full_match_data_with_scoreboard_endpoint(match_id: int):
            self.logger.debug("Get full_match_data_with_scoreboard by match endpoint")
            from src.helpers.fetch_helpers import fetch_with_scoreboard_data

            return await fetch_with_scoreboard_data(match_id)

        @router.post("/id/{match_id}/upload_team_logo", response_model=UploadTeamLogoResponse)
        async def upload_team_logo(match_id: int, file: UploadFile = File(...)):
            file_location = await file_service.save_upload_image(
                file, sub_folder=f"match/{match_id}/teams_logos"
            )
            self.logger.debug(f"Upload team in match logo endpoint file location: {file_location}")
            return {"logoUrl": file_location}

        @router.post(
            "/id/{match_id}/upload_resize_logo",
            response_model=UploadResizeTeamLogoResponse,
        )
        async def upload_resize_team_logo(match_id: int, file: UploadFile = File(...)):
            uploaded_paths = await file_service.save_and_resize_upload_image(
                file,
                sub_folder=f"match/{match_id}/teams_logos",
                icon_height=100,
                web_view_height=400,
            )
            self.logger.debug(
                f"Upload and resize team in match logo endpoint file location: {uploaded_paths}"
            )
            return uploaded_paths

        @router.post("/add")
        async def create_match_with_full_data_and_scoreboard_endpoint(
            data: MatchSchemaCreate,
        ):
            self.logger.debug(f"Creat match with full data and scoreboard endpoint {data}")
            teams_service = self.service_registry.get("team")
            tournament_service = self.service_registry.get("tournament")
            sponsor_service = self.service_registry.get("sponsor")
            match_db_service = self.service_registry.get("matchdata")
            playclock_service = self.service_registry.get("playclock")
            gameclock_service = self.service_registry.get("gameclock")
            scoreboard_db_service = self.service_registry.get("scoreboard")

            try:
                self.logger.debug(f"Creating simple match: {data}")
                new_match = await self.service.create_or_update_match(data)

                self.logger.debug("Creating default matchdata, playclock and gameclock")
                default_match_data = MatchDataSchemaCreate(match_id=new_match.id)
                default_playclock = PlayClockSchemaCreate(match_id=new_match.id)
                default_gameclock = GameClockSchemaCreate(match_id=new_match.id)

                self.logger.debug("Get tournament and tournament main sponsor")
                tournament = await tournament_service.get_by_id(new_match.tournament_id)
                tournament_main_sponsor = await sponsor_service.get_by_id(
                    tournament.main_sponsor_id
                )
                self.logger.debug("Get teams for match")
                team_a = await teams_service.get_by_id(new_match.team_a_id)
                team_b = await teams_service.get_by_id(new_match.team_b_id)

                scale_main_sponsor = (
                    tournament_main_sponsor.scale_logo if tournament_main_sponsor else 2.0
                )
                self.logger.debug("If scoreboard exist")
                existing_scoreboard = await scoreboard_db_service.get_scoreboard_by_match_id(
                    new_match.id
                )

                scoreboard_schema: ScoreboardSchemaCreate | ScoreboardSchemaUpdate  # type: ignore[assignment]
                if existing_scoreboard is None:
                    scoreboard_schema = ScoreboardSchemaCreate(
                        match_id=new_match.id,
                        scale_tournament_logo=2,
                        scale_main_sponsor=scale_main_sponsor,
                        scale_logo_a=2,
                        scale_logo_b=2,
                        team_a_game_color=team_a.team_color,
                        team_b_game_color=team_b.team_color,
                        team_a_game_title=team_a.title.title(),
                        team_b_game_title=team_b.title.title(),
                    )
                else:
                    scoreboard_schema = ScoreboardSchemaUpdate(
                        match_id=new_match.id,
                        scale_tournament_logo=2,
                        scale_main_sponsor=scale_main_sponsor,
                        scale_logo_a=2,
                        scale_logo_b=2,
                        team_a_game_color=team_a.team_color,
                        team_b_game_color=team_b.team_color,
                        team_a_game_title=team_a.title.title(),
                        team_b_game_title=team_b.title.title(),
                    )
                new_scoreboard = await scoreboard_db_service.create_or_update_scoreboard(
                    scoreboard_schema
                )
                self.logger.debug(f"Scoreboard created or updated: {new_scoreboard.__dict__}")

                new_match_data = await match_db_service.create(default_match_data)
                await self.service.get_teams_by_match(new_match_data.match_id)
                await playclock_service.create(default_playclock)
                await gameclock_service.create(default_gameclock)
                self.logger.info(
                    f"Created match with full data and scoreboard {MatchSchema.model_validate(new_match)}"
                )
                return MatchSchema.model_validate(new_match)
            except Exception as e:
                self.logger.error(
                    f"Error creating match with full data and scoreboard: {str(e)}",
                    exc_info=True,
                )

        @router.get(
            "/id/{match_id}/stats/",
            summary="Get match statistics",
            description="Get complete match statistics for both teams including team, offense, QB, and defense stats",
            responses={
                200: {"description": "Stats retrieved successfully"},
                404: {"description": "Match not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def get_match_stats_endpoint(match_id: int):
            self.logger.debug(f"Get match stats endpoint for match_id:{match_id}")
            stats_service = self.get_match_stats_service()

            try:
                stats = await stats_service.get_match_with_cached_stats(match_id)
                if not stats:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Match {match_id} not found or no stats available",
                    )
                return stats
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(f"Error fetching stats for match {match_id}: {ex}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error")

        return router
