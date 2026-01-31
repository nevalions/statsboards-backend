from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import require_roles
from src.core import BaseRouter, db
from src.core.models import PlayerMatchDB
from src.core.service_registry import get_service_registry
from src.helpers.photo_utils import photo_files_exist

from ..logging_config import get_logger
from ..matches.schemas import MatchSchemaBase
from ..pars_eesl.pars_all_players_from_eesl import collect_player_full_data_eesl
from ..pars_eesl.pars_match import ParsedMatch, logger, parse_match_and_create_jsons
from ..person.schemas import PersonSchemaCreate
from ..player.schemas import PlayerSchema, PlayerSchemaCreate
from ..player_team_tournament.schemas import (
    PlayerTeamTournamentSchema,
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)
from ..positions.schemas import PositionSchemaBase, PositionSchemaCreate
from ..teams.schemas import TeamSchemaBase
from .db_services import PlayerMatchServiceDB
from .schemas import PlayerMatchSchema, PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate


class PlayerMatchAPIRouter(
    BaseRouter[
        PlayerMatchSchema,
        PlayerMatchSchemaCreate,
        PlayerMatchSchemaUpdate,
    ]
):
    def __init__(self, service: PlayerMatchServiceDB):
        super().__init__("/api/players_match", ["players_match"], service)
        self.logger = get_logger("PlayerMatchAPIRouter", self)
        self.logger.debug("Initialized PlayerMatchAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerMatchSchema,
        )
        async def create_player_match_endpoint(
            player_match: PlayerMatchSchemaCreate,
        ):
            try:
                self.logger.debug(f"Create player in match endpoint with data: {player_match}")
                new_player_match = await self.service.create_or_update_player_match(player_match)
                if new_player_match:
                    return PlayerMatchSchema.model_validate(new_player_match)
                else:
                    raise HTTPException(status_code=409, detail="Player in match creation fail")
            except Exception as ex:
                self.logger.error(
                    f"Error creating player in match endpoint with data: {player_match}",
                    exc_info=ex,
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerMatchSchema,
        )
        async def get_player_match_by_eesl_id_endpoint(
            eesl_id: int,
        ):
            try:
                self.logger.debug(f"Get player in match endpoint with eesl_id:{eesl_id}")
                player_match = await self.service.get_player_match_by_eesl_id(value=eesl_id)
                if player_match is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Player match eesl_id({eesl_id}) not found",
                    )
                return PlayerMatchSchema.model_validate(player_match)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting player in match with match eesl_id {eesl_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(status_code=500, detail="Internal server error") from ex

        @router.put(
            "/{item_id}/",
            response_model=PlayerMatchSchema,
        )
        async def update_player_match_endpoint(
            item_id: int,
            item: PlayerMatchSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Update player in match endpoint with data: {item}")
                update_ = await self.service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Player team tournament id {item_id} not found",
                    )
                return PlayerMatchSchema.model_validate(update_)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(f"Error updating player in match with data: {item}", exc_info=ex)
                raise HTTPException(
                    status_code=500, detail="Internal server error updating player match"
                ) from ex

        @router.get(
            "/id/{player_id}/player_in_sport/",
            response_model=PlayerSchema,
        )
        async def get_player_in_sport_endpoint(player_id: int):
            self.logger.debug(f"Get player in sport endpoint with player id:{player_id}")
            return await self.service.get_player_in_sport(player_id)

        @router.get(
            "/id/{player_id}/player_in_team_tournament/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_team_tournament_endpoint(player_id: int):
            self.logger.debug(f"Get player in tournament endpoint with player id:{player_id}")
            return await self.service.get_player_in_team_tournament(player_id)

        @router.get(
            "/id/{player_id}/full_data/",
            # response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_match_full_data_endpoint(player_id: int):
            self.logger.debug(f"Get player in match full data endpoint with player id:{player_id}")
            return await self.service.get_player_in_match_full_data(player_id)

        @router.get(
            "/pars/match/{eesl_match_id}",
            # response_model=List[TournamentSchemaCreate],
        )
        async def get_parsed_eesl_match_endpoint(eesl_match_id: int):
            self.logger.debug(f"Get parsed eesl match endpoint with eesl_id:{eesl_match_id}")
            return await parse_match_and_create_jsons(eesl_match_id)

        @router.get("/pars_and_create/match/{eesl_match_id}")
        async def create_parsed_eesl_match_endpoint(
            eesl_match_id: int,
        ):
            self.logger.debug(f"Start parsing eesl match endpoint with eesl_id:{eesl_match_id}")
            from ..matches.db_services import MatchServiceDB
            from ..person.db_services import PersonServiceDB
            from ..player.db_services import PlayerServiceDB
            from ..player_team_tournament.db_services import (
                PlayerTeamTournamentServiceDB,
            )
            from ..positions.db_services import PositionServiceDB
            from ..teams.db_services import TeamServiceDB

            try:
                # Get database from service registry for correct event loop context
                registry = get_service_registry()
                database = registry.database

                parsed_match: ParsedMatch = await parse_match_and_create_jsons(eesl_match_id)
                match_service = MatchServiceDB(database)
                position_service = PositionServiceDB(database)
                match: MatchSchemaBase = await match_service.get_match_by_eesl_id(eesl_match_id)
                team_a: TeamSchemaBase = await TeamServiceDB(database).get_team_by_eesl_id(
                    parsed_match["team_a_eesl_id"]
                )
                team_b: TeamSchemaBase = await TeamServiceDB(database).get_team_by_eesl_id(
                    parsed_match["team_b_eesl_id"]
                )

                created_players_match = []

                if parsed_match and match:
                    self.logger.debug("Got parse match and match in db")
                    existing_player_ids = set()
                    for home_player in parsed_match["roster_a"]:
                        player_position = home_player.get("player_position", "").strip()
                        if not player_position:
                            self.logger.debug(
                                f"Skipping home player {home_player.get('player_eesl_id')} - no position"
                            )
                            continue

                        try:
                            position: PositionSchemaBase = (
                                await position_service.get_position_by_title(player_position)
                            )
                        except HTTPException:
                            self.logger.debug("No position found for home player")
                            position_schema = {
                                "title": player_position,
                                "sport_id": 1,
                            }
                            self.logger.debug("Creating new position for home player")
                            position = await PositionServiceDB(database).create(
                                PositionSchemaCreate(**position_schema)
                            )
                        person = await PersonServiceDB(database).get_person_by_eesl_id(
                            home_player["player_eesl_id"]
                        )
                        needs_photo_download = (
                            person is None
                            or not person.person_photo_url
                            or not person.person_photo_icon_url
                            or not person.person_photo_web_url
                            or not photo_files_exist(person.person_photo_url)
                        )
                        if person is None:
                            self.logger.debug("No person for home player")
                        elif needs_photo_download:
                            self.logger.debug(
                                f"Person exists but missing photos for {home_player['player_eesl_id']}"
                            )

                        if needs_photo_download:
                            player_in_team = await collect_player_full_data_eesl(
                                home_player["player_eesl_id"]
                            )
                            if player_in_team is None:
                                self.logger.warning(
                                    f"Failed to fetch player data for {home_player['player_eesl_id']}, skipping"
                                )
                                continue
                            person_schema = PersonSchemaCreate(**player_in_team["person"])
                            self.logger.debug("Creating/updating person for home player")
                            person = await PersonServiceDB(database).create_or_update_person(
                                person_schema
                            )

                        player = await PlayerServiceDB(database).get_player_by_eesl_id(
                            home_player["player_eesl_id"]
                        )
                        if player is None:
                            self.logger.debug("No player for home match player")
                            player_schema = PlayerSchemaCreate(
                                **{
                                    "sport_id": 1,
                                    "person_id": person.id,
                                    "player_eesl_id": home_player["player_eesl_id"],
                                }
                            )
                            self.logger.debug("Creating new player for home player")
                            player = await PlayerServiceDB(database).create_or_update_player(
                                player_schema
                            )

                        player_in_team = await PlayerTeamTournamentServiceDB(
                            database
                        ).get_player_team_tournament_by_eesl_id(home_player["player_eesl_id"])

                        if player_in_team is None:
                            self.logger.debug("No player in team for home player")
                            created_player_in_team_schema = PlayerTeamTournamentSchemaCreate(
                                **{
                                    "player_team_tournament_eesl_id": home_player["player_eesl_id"],
                                    "player_id": player.id,
                                    "position_id": position.id,
                                    "team_id": team_a.id,
                                    "tournament_id": match.tournament_id,
                                    "player_number": home_player["player_number"],
                                }
                            )
                            self.logger.debug("Creating new player in team for home player")
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                database
                            ).create_or_update_player_team_tournament(created_player_in_team_schema)
                        else:
                            self.logger.debug("Player exists in team for home player, updating")
                            updated_player_in_team_schema = PlayerTeamTournamentSchemaUpdate(
                                **{
                                    "player_team_tournament_eesl_id": home_player["player_eesl_id"],
                                    "player_id": player.id,
                                    "position_id": position.id,
                                    "team_id": team_a.id,
                                    "tournament_id": match.tournament_id,
                                    "player_number": home_player["player_number"],
                                }
                            )
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                database
                            ).create_or_update_player_team_tournament(updated_player_in_team_schema)

                        if team_a is None or player_in_team is None:
                            self.logger.debug("No team for home player, continue")
                            continue

                        player_eesl_id = home_player.get("player_eesl_id")
                        if player_eesl_id in existing_player_ids:
                            self.logger.debug("No eesl id for home player, skipping")
                            continue

                        existing_player_ids.add(player_eesl_id)
                        player_schema = {
                            "player_match_eesl_id": player_eesl_id,
                            "player_team_tournament_id": player_in_team.id,
                            "match_position_id": position.id,
                            "match_id": match.id,
                            "match_number": home_player["player_number"],
                            "team_id": team_a.id,
                            "is_start": False,
                        }

                        exist_player_in_match = (
                            await self.service.get_player_match_by_match_id_and_eesl_id(
                                player_schema["match_id"],
                                player_schema["player_match_eesl_id"],
                            )
                        )

                        if exist_player_in_match:
                            self.logger.debug("Player in match exist")
                            if exist_player_in_match.is_start:
                                self.logger.warning("Player in match is in Start")
                                player_schema["player_match_eesl_id"] = (
                                    exist_player_in_match.player_match_eesl_id
                                )
                                player_schema["player_team_tournament_id"] = (
                                    exist_player_in_match.player_team_tournament_id
                                )
                                player_schema["match_position_id"] = (
                                    exist_player_in_match.match_position_id
                                )
                                player_schema["match_id"] = exist_player_in_match.match_id
                                player_schema["match_number"] = exist_player_in_match.match_number
                                player_schema["team_id"] = exist_player_in_match.team_id
                                player_schema["is_start"] = True
                                position = await PositionServiceDB(database).get_by_id(
                                    exist_player_in_match.match_position_id
                                )

                        player = PlayerMatchSchemaCreate(**player_schema)
                        created_player = await self.service.create_or_update_player_match(player)
                        created_players_match.append(
                            {
                                "match_player": created_player,
                                "person": person,
                                "player_team_tournament": player_in_team,
                                "position": position,
                            }
                        )

                    for away_player in parsed_match["roster_b"]:
                        player_position = away_player.get("player_position", "").strip()
                        if not player_position:
                            self.logger.debug(
                                f"Skipping away player {away_player.get('player_eesl_id')} - no position"
                            )
                            continue

                        try:
                            position = await position_service.get_position_by_title(player_position)
                        except HTTPException:
                            self.logger.debug("No position for away player")
                            position_schema = {
                                "title": player_position,
                                "sport_id": 1,
                            }
                            self.logger.debug("Creating new position for away player")
                            position = await PositionServiceDB(database).create(
                                PositionSchemaCreate(**position_schema)
                            )
                        person = await PersonServiceDB(database).get_person_by_eesl_id(
                            away_player["player_eesl_id"]
                        )
                        needs_photo_download = (
                            person is None
                            or not person.person_photo_url
                            or not person.person_photo_icon_url
                            or not person.person_photo_web_url
                            or not photo_files_exist(person.person_photo_url)
                        )
                        if person is None:
                            self.logger.debug("No person for away player")
                        elif needs_photo_download:
                            self.logger.debug(
                                f"Person exists but missing photos for {away_player['player_eesl_id']}"
                            )

                        if needs_photo_download:
                            player_in_team = await collect_player_full_data_eesl(
                                away_player["player_eesl_id"]
                            )
                            if player_in_team is None:
                                self.logger.warning(
                                    f"Failed to fetch player data for {away_player['player_eesl_id']}, skipping"
                                )
                                continue
                            person_schema = PersonSchemaCreate(**player_in_team["person"])
                            self.logger.debug("Creating/updating person for away player")
                            person = await PersonServiceDB(database).create_or_update_person(
                                person_schema
                            )

                        player = await PlayerServiceDB(database).get_player_by_eesl_id(
                            away_player["player_eesl_id"]
                        )
                        if player is None:
                            self.logger.debug("No player for away match player")
                            player_schema = PlayerSchemaCreate(
                                **{
                                    "sport_id": 1,
                                    "person_id": person.id,
                                    "player_eesl_id": away_player["player_eesl_id"],
                                }
                            )
                            self.logger.debug("Creating new player for away player")
                            player = await PlayerServiceDB(database).create_or_update_player(
                                player_schema
                            )

                        player_in_team = await PlayerTeamTournamentServiceDB(
                            database
                        ).get_player_team_tournament_by_eesl_id(away_player["player_eesl_id"])

                        if player_in_team is None:
                            created_player_in_team_schema = PlayerTeamTournamentSchemaCreate(
                                **{
                                    "player_team_tournament_eesl_id": away_player["player_eesl_id"],
                                    "player_id": player.id,
                                    "position_id": position.id,
                                    "team_id": team_b.id,
                                    "tournament_id": match.tournament_id,
                                    "player_number": away_player["player_number"],
                                }
                            )
                            logger.debug("Creating new player in team for away player")
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                database
                            ).create_or_update_player_team_tournament(created_player_in_team_schema)
                        else:
                            logger.debug("Player in team exists, updating player")
                            updated_player_in_team_schema = PlayerTeamTournamentSchemaUpdate(
                                **{
                                    "player_team_tournament_eesl_id": away_player["player_eesl_id"],
                                    "player_id": player.id,
                                    "position_id": position.id,
                                    "team_id": team_b.id,
                                    "tournament_id": match.tournament_id,
                                    "player_number": away_player["player_number"],
                                }
                            )
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                database
                            ).create_or_update_player_team_tournament(updated_player_in_team_schema)

                        # player_in_team = await PlayerTeamTournamentServiceDB(db).get_player_team_tournament_by_eesl_id(
                        #     away_player['player_eesl_id'])

                        if team_b is None or player_in_team is None:
                            self.logger.debug("No team for away player, continue")
                            continue

                        player_eesl_id = away_player.get("player_eesl_id")
                        if player_eesl_id in existing_player_ids:
                            self.logger.debug("No eesl id for away player, skipping")
                            continue

                        existing_player_ids.add(player_eesl_id)
                        player_schema = {
                            "player_match_eesl_id": player_eesl_id,
                            "player_team_tournament_id": player_in_team.id,
                            "match_position_id": position.id,
                            "match_id": match.id,
                            "match_number": away_player["player_number"],
                            "team_id": team_b.id,
                            "is_start": False,
                        }

                        exist_player_in_match = (
                            await self.service.get_player_match_by_match_id_and_eesl_id(
                                player_schema["match_id"],
                                player_schema["player_match_eesl_id"],
                            )
                        )

                        if exist_player_in_match:
                            self.logger.debug("Player in already in match")
                            if exist_player_in_match.is_start:
                                self.logger.warning("Player in start")
                                player_schema["player_match_eesl_id"] = (
                                    exist_player_in_match.player_match_eesl_id
                                )
                                player_schema["player_team_tournament_id"] = (
                                    exist_player_in_match.player_team_tournament_id
                                )
                                player_schema["match_position_id"] = (
                                    exist_player_in_match.match_position_id
                                )
                                player_schema["match_id"] = exist_player_in_match.match_id
                                player_schema["match_number"] = exist_player_in_match.match_number
                                player_schema["team_id"] = exist_player_in_match.team_id
                                player_schema["is_start"] = True
                                position = await PositionServiceDB(database).get_by_id(
                                    exist_player_in_match.match_position_id
                                )

                        self.logger.debug("Creating player in match")
                        player = PlayerMatchSchemaCreate(**player_schema)
                        created_player = await self.service.create_or_update_player_match(player)
                        created_players_match.append(
                            {
                                "match_player": created_player,
                                "person": person,
                                "player_team_tournament": player_in_team,
                                "position": position,
                            }
                        )

                    return created_players_match
                else:
                    return []
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(f"Error parsing eesl match {ex}", exc_info=True)
                return []

        @router.delete(
            "/id/{model_id}",
            summary="Delete player match",
            description="Delete a player match by ID. Requires admin role.",
            responses={
                200: {"description": "PlayerMatch deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "PlayerMatch not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_player_match_endpoint(
            model_id: int,
            _: Annotated[PlayerMatchDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete player match endpoint id:{model_id}")
            await self.service.delete(model_id)
            return {"detail": f"PlayerMatch {model_id} deleted successfully"}

        return router


api_player_match_router = PlayerMatchAPIRouter(PlayerMatchServiceDB(db)).route()
