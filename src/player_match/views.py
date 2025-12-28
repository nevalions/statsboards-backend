from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerMatchServiceDB
from .schemas import PlayerMatchSchema, PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from ..logging_config import setup_logging, get_logger
from ..matches.schemas import MatchSchemaBase
from ..pars_eesl.pars_all_players_from_eesl import collect_player_full_data_eesl
from ..pars_eesl.pars_match import parse_match_and_create_jsons, ParsedMatch, logger
from ..person.schemas import PersonSchemaCreate
from ..player.schemas import PlayerSchema, PlayerSchemaCreate
from ..player_team_tournament.schemas import (
    PlayerTeamTournamentSchema,
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)
from ..positions.schemas import PositionSchemaCreate, PositionSchemaBase
from ..teams.schemas import TeamSchemaBase

setup_logging()


class PlayerMatchAPIRouter(
    BaseRouter[
        PlayerMatchSchema,
        PlayerMatchSchemaCreate,
        PlayerMatchSchemaUpdate,
    ]
):
    def __init__(self, service: PlayerMatchServiceDB):
        super().__init__("/api/players_match", ["players_match"], service)
        self.logger = get_logger("backend_logger_PlayerMatchAPIRouter", self)
        self.logger.debug(f"Initialized PlayerMatchAPIRouter")

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
                self.logger.debug(
                    f"Create player in match endpoint with data: {player_match}"
                )
                new_player_match = await self.service.create_or_update_player_match(
                    player_match
                )
                if new_player_match:
                    return new_player_match.__dict__
                else:
                    raise HTTPException(
                        status_code=409, detail=f"Player in match creation fail"
                    )
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
            player_match_eesl_id: int,
        ):
            try:
                self.logger.debug(
                    f"Get player in match endpoint with eesl_id:{player_match_eesl_id}"
                )
                tournament = await self.service.get_player_match_by_eesl_id(
                    value=player_match_eesl_id
                )
                if tournament is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Tournament eesl_id({player_match_eesl_id}) not found",
                    )
                return tournament.__dict__
            except Exception as ex:
                self.logger.error(
                    f"Error getting player in match with match eesl_id {player_match_eesl_id} {ex}",
                    exc_info=ex,
                )

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
                update_ = await self.service.update_player_match(item_id, item)
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Player team tournament id {item_id} not found",
                    )
                return update_.__dict__
            except Exception as ex:
                self.logger.error(
                    f"Error updating player in match with data: {item}", exc_info=ex
                )

        @router.get(
            "/id/{player_id}/player_in_sport/",
            response_model=PlayerSchema,
        )
        async def get_player_in_sport_endpoint(player_id: int):
            self.logger.debug(
                f"Get player in sport endpoint with player id:{player_id}"
            )
            return await self.service.get_player_in_sport(player_id)

        @router.get(
            "/id/{player_id}/player_in_team_tournament/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_team_tournament_endpoint(player_id: int):
            self.logger.debug(
                f"Get player in tournament endpoint with player id:{player_id}"
            )
            return await self.service.get_player_in_team_tournament(player_id)

        @router.get(
            "/id/{player_id}/full_data/",
            # response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_match_full_data_endpoint(player_id: int):
            self.logger.debug(
                f"Get player in match full data endpoint with player id:{player_id}"
            )
            return await self.service.get_player_in_match_full_data(player_id)

        @router.get(
            "/pars/match/{eesl_match_id}",
            # response_model=List[TournamentSchemaCreate],
        )
        async def get_parsed_eesl_match_endpoint(eesl_match_id: int):
            self.logger.debug(
                f"Get parsed eesl match endpoint with eesl_id:{eesl_match_id}"
            )
            return await parse_match_and_create_jsons(eesl_match_id)

        @router.get("/pars_and_create/match/{eesl_match_id}")
        async def create_parsed_eesl_match_endpoint(
            eesl_match_id: int,
        ):
            self.logger.debug(
                f"Start parsing eesl match endpoint with eesl_id:{eesl_match_id}"
            )
            from ..matches.db_services import MatchServiceDB
            from ..positions.db_services import PositionServiceDB
            from ..teams.db_services import TeamServiceDB
            from ..person.db_services import PersonServiceDB
            from ..player.db_services import PlayerServiceDB
            from ..player_team_tournament.db_services import (
                PlayerTeamTournamentServiceDB,
            )

            try:
                parsed_match: ParsedMatch = await parse_match_and_create_jsons(
                    eesl_match_id
                )
                match_service = MatchServiceDB(db)
                position_service = PositionServiceDB(db)
                match: MatchSchemaBase = await match_service.get_match_by_eesl_id(
                    eesl_match_id
                )
                team_a: TeamSchemaBase = await TeamServiceDB(db).get_team_by_eesl_id(
                    parsed_match["team_a_eesl_id"]
                )
                team_b: TeamSchemaBase = await TeamServiceDB(db).get_team_by_eesl_id(
                    parsed_match["team_b_eesl_id"]
                )

                created_players_match = []

                if parsed_match and match:
                    self.logger.debug(f"Got parse match and match in db")
                    existing_player_ids = set()
                    for home_player in parsed_match["roster_a"]:
                        position: PositionSchemaBase = (
                            await position_service.get_position_by_title(
                                home_player["player_position"]
                            )
                        )
                        if position is None:
                            self.logger.debug(f"No position found for home player")
                            position_schema = {
                                "title": home_player["player_position"],
                                "sport_id": 1,
                            }
                            self.logger.debug(f"Creating new position for home player")
                            position = await PositionServiceDB(db).create_new_position(
                                PositionSchemaCreate(**position_schema)
                            )
                        person = await PersonServiceDB(db).get_person_by_eesl_id(
                            home_player["player_eesl_id"]
                        )
                        if person is None:
                            self.logger.debug(f"No person for home player")
                            player_in_team = await collect_player_full_data_eesl(
                                home_player["player_eesl_id"]
                            )
                            person_schema = PersonSchemaCreate(
                                **player_in_team["person"]
                            )
                            self.logger.debug(f"Creating new person for home player")
                            person = await PersonServiceDB(db).create_or_update_person(
                                person_schema
                            )

                        player = await PlayerServiceDB(db).get_player_by_eesl_id(
                            home_player["player_eesl_id"]
                        )
                        if player is None:
                            self.logger.debug(f"No player for home match player")
                            player_schema = PlayerSchemaCreate(
                                **{
                                    "sport_id": 1,
                                    "person_id": person.id,
                                    "player_eesl_id": home_player["player_eesl_id"],
                                }
                            )
                            self.logger.debug(f"Creating new player for home player")
                            player = await PlayerServiceDB(db).create_or_update_player(
                                player_schema
                            )

                        player_in_team = await PlayerTeamTournamentServiceDB(
                            db
                        ).get_player_team_tournament_by_eesl_id(
                            home_player["player_eesl_id"]
                        )

                        if player_in_team is None:
                            self.logger.debug(f"No player in team for home player")
                            created_player_in_team_schema = (
                                PlayerTeamTournamentSchemaCreate(
                                    **{
                                        "player_team_tournament_eesl_id": home_player[
                                            "player_eesl_id"
                                        ],
                                        "player_id": player.id,
                                        "position_id": position.id,
                                        "team_id": team_a.id,
                                        "tournament_id": match.tournament_id,
                                        "player_number": home_player["player_number"],
                                    }
                                )
                            )
                            self.logger.debug(
                                f"Creating new player in team for home player"
                            )
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                db
                            ).create_or_update_player_team_tournament(
                                created_player_in_team_schema
                            )
                        else:
                            self.logger.debug(
                                f"Player exists in team for home player, updating"
                            )
                            updated_player_in_team_schema = (
                                PlayerTeamTournamentSchemaUpdate(
                                    **{
                                        "player_team_tournament_eesl_id": home_player[
                                            "player_eesl_id"
                                        ],
                                        "player_id": player.id,
                                        "position_id": position.id,
                                        "team_id": team_a.id,
                                        "tournament_id": match.tournament_id,
                                        "player_number": home_player["player_number"],
                                    }
                                )
                            )
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                db
                            ).create_or_update_player_team_tournament(
                                updated_player_in_team_schema
                            )

                        if team_a is None or player_in_team is None:
                            self.logger.debug(f"No team for home player, continue")
                            continue

                        player_eesl_id = home_player.get("player_eesl_id")
                        if player_eesl_id in existing_player_ids:
                            self.logger.debug(f"No eesl id for home player, skipping")
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
                            self.logger.debug(f"Player in match exist")
                            if exist_player_in_match.is_start:
                                self.logger.warning(f"Player in match is in Start")
                                player_schema[
                                    "player_match_eesl_id"
                                ] = exist_player_in_match.player_match_eesl_id
                                player_schema[
                                    "player_team_tournament_id"
                                ] = exist_player_in_match.player_team_tournament_id
                                player_schema[
                                    "match_position_id"
                                ] = exist_player_in_match.match_position_id
                                player_schema[
                                    "match_id"
                                ] = exist_player_in_match.match_id
                                player_schema[
                                    "match_number"
                                ] = exist_player_in_match.match_number
                                player_schema["team_id"] = exist_player_in_match.team_id
                                player_schema["is_start"] = True
                                position = await PositionServiceDB(db).get_by_id(
                                    exist_player_in_match.match_position_id
                                )

                        player = PlayerMatchSchemaCreate(**player_schema)
                        created_player = (
                            await self.service.create_or_update_player_match(player)
                        )
                        created_players_match.append(
                            {
                                "match_player": created_player,
                                "person": person,
                                "player_team_tournament": player_in_team,
                                "position": position,
                            }
                        )

                    for away_player in parsed_match["roster_b"]:
                        position = await position_service.get_position_by_title(
                            away_player["player_position"]
                        )
                        if position is None:
                            self.logger.debug(f"No position for away player")
                            position_schema = {
                                "title": away_player["player_position"],
                                "sport_id": 1,
                            }
                            self.logger.debug(f"Creating new position for away player")
                            position = await PositionServiceDB(db).create_new_position(
                                PositionSchemaCreate(**position_schema)
                            )
                        person = await PersonServiceDB(db).get_person_by_eesl_id(
                            away_player["player_eesl_id"]
                        )
                        if person is None:
                            self.logger.debug(f"No person for away player")
                            player_in_team = await collect_player_full_data_eesl(
                                away_player["player_eesl_id"]
                            )
                            person_schema = PersonSchemaCreate(
                                **player_in_team["person"]
                            )
                            self.logger.debug(f"Creating new person for away player")
                            person = await PersonServiceDB(db).create_or_update_person(
                                person_schema
                            )

                        player = await PlayerServiceDB(db).get_player_by_eesl_id(
                            away_player["player_eesl_id"]
                        )
                        if player is None:
                            self.logger.debug(f"No player for away match player")
                            player_schema = PlayerSchemaCreate(
                                **{
                                    "sport_id": 1,
                                    "person_id": person.id,
                                    "player_eesl_id": away_player["player_eesl_id"],
                                }
                            )
                            self.logger.debug(f"Creating new player for away player")
                            player = await PlayerServiceDB(db).create_or_update_player(
                                player_schema
                            )

                        player_in_team = await PlayerTeamTournamentServiceDB(
                            db
                        ).get_player_team_tournament_by_eesl_id(
                            away_player["player_eesl_id"]
                        )

                        if player_in_team is None:
                            created_player_in_team_schema = (
                                PlayerTeamTournamentSchemaCreate(
                                    **{
                                        "player_team_tournament_eesl_id": away_player[
                                            "player_eesl_id"
                                        ],
                                        "player_id": player.id,
                                        "position_id": position.id,
                                        "team_id": team_b.id,
                                        "tournament_id": match.tournament_id,
                                        "player_number": away_player["player_number"],
                                    }
                                )
                            )
                            logger.debug(f"Creating new player in team for away player")
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                db
                            ).create_or_update_player_team_tournament(
                                created_player_in_team_schema
                            )
                        else:
                            logger.debug(f"Player in team exists, updating player")
                            updated_player_in_team_schema = (
                                PlayerTeamTournamentSchemaUpdate(
                                    **{
                                        "player_team_tournament_eesl_id": away_player[
                                            "player_eesl_id"
                                        ],
                                        "player_id": player.id,
                                        "position_id": position.id,
                                        "team_id": team_b.id,
                                        "tournament_id": match.tournament_id,
                                        "player_number": away_player["player_number"],
                                    }
                                )
                            )
                            player_in_team = await PlayerTeamTournamentServiceDB(
                                db
                            ).create_or_update_player_team_tournament(
                                updated_player_in_team_schema
                            )

                        # player_in_team = await PlayerTeamTournamentServiceDB(db).get_player_team_tournament_by_eesl_id(
                        #     away_player['player_eesl_id'])

                        if team_b is None or player_in_team is None:
                            self.logger.debug(f"No team for away player, continue")
                            continue

                        player_eesl_id = away_player.get("player_eesl_id")
                        if player_eesl_id in existing_player_ids:
                            self.logger.debug(f"No eesl id for away player, skipping")
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
                            self.logger.debug(f"Player in already in match")
                            if exist_player_in_match.is_start:
                                self.logger.warning(f"Player in start")
                                player_schema[
                                    "player_match_eesl_id"
                                ] = exist_player_in_match.player_match_eesl_id
                                player_schema[
                                    "player_team_tournament_id"
                                ] = exist_player_in_match.player_team_tournament_id
                                player_schema[
                                    "match_position_id"
                                ] = exist_player_in_match.match_position_id
                                player_schema[
                                    "match_id"
                                ] = exist_player_in_match.match_id
                                player_schema[
                                    "match_number"
                                ] = exist_player_in_match.match_number
                                player_schema["team_id"] = exist_player_in_match.team_id
                                player_schema["is_start"] = True
                                position = await PositionServiceDB(db).get_by_id(
                                    exist_player_in_match.match_position_id
                                )

                        self.logger.debug(f"Creating player in match")
                        player = PlayerMatchSchemaCreate(**player_schema)
                        created_player = (
                            await self.service.create_or_update_player_match(player)
                        )
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
            except Exception as ex:
                self.logger.error(f"Error parsing eesl match {ex}", exc_info=True)

        return router


api_player_match_router = PlayerMatchAPIRouter(PlayerMatchServiceDB(db)).route()
