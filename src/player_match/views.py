from pprint import pprint

from fastapi import HTTPException

from src.core import BaseRouter, db
from .db_services import PlayerMatchServiceDB
from .schemas import PlayerMatchSchema, PlayerMatchSchemaCreate, PlayerMatchSchemaUpdate
from ..pars_eesl.pars_all_players_from_eesl import collect_player_full_data_eesl
from ..pars_eesl.pars_match import parse_match_and_create_jsons
from ..person.schemas import PersonSchemaCreate
from ..player.schemas import PlayerSchema, PlayerSchemaCreate
from ..player_team_tournament.schemas import (
    PlayerTeamTournamentSchema,
    PlayerTeamTournamentSchemaCreate,
)
from ..positions.schemas import PositionSchemaCreate


# Person backend
class PlayerMatchAPIRouter(
    BaseRouter[
        PlayerMatchSchema,
        PlayerMatchSchemaCreate,
        PlayerMatchSchemaUpdate,
    ]
):
    def __init__(self, service: PlayerMatchServiceDB):
        super().__init__("/api/players_match", ["players_match"], service)

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerMatchSchema,
        )
        async def create_player_match_endpoint(
            player_match: PlayerMatchSchemaCreate,
        ):
            print(f"Received player_match: {player_match}")
            new_player_match = await self.service.create_or_update_player_match(
                player_match
            )
            if new_player_match:
                return new_player_match.__dict__
            else:
                raise HTTPException(status_code=409, detail=f"Person creation fail")

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerMatchSchema,
        )
        async def get_player_match_by_eesl_id_endpoint(
            player_match_eesl_id: int,
        ):
            tournament = await self.service.get_player_match_by_eesl_id(
                value=player_match_eesl_id
            )
            if tournament is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tournament eesl_id({player_match_eesl_id}) " f"not found",
                )
            return tournament.__dict__

        @router.put(
            "/{item_id}/",
            response_model=PlayerMatchSchema,
        )
        async def update_player_match_endpoint(
            item_id: int,
            item: PlayerMatchSchemaUpdate,
        ):
            update_ = await self.service.update_player_match(item_id, item)
            if update_ is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Player team tournament id {item_id} not found",
                )
            return update_.__dict__

        @router.get(
            "/id/{player_id}/player_in_sport/",
            response_model=PlayerSchema,
        )
        async def get_player_in_sport_endpoint(player_id: int):
            return await self.service.get_player_in_sport(player_id)

        @router.get(
            "/id/{player_id}/player_in_team_tournament/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_team_tournament_endpoint(player_id: int):
            return await self.service.get_player_in_team_tournament(player_id)

        @router.get(
            "/id/{player_id}/full_data/",
            # response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_in_match_full_data_endpoint(player_id: int):
            return await self.service.get_player_in_match_full_data(player_id)

        @router.get(
            "/pars/match/{eesl_match_id}",
            # response_model=List[TournamentSchemaCreate],
        )
        async def get_parsed_eesl_match_endpoint(eesl_match_id: int):
            return await parse_match_and_create_jsons(eesl_match_id)

        @router.get("/pars_and_create/match/{eesl_match_id}")
        async def create_parsed_eesl_match_endpoint(
            eesl_match_id: int,
        ):
            from ..matches.db_services import MatchServiceDB
            from ..positions.db_services import PositionServiceDB
            from ..teams.db_services import TeamServiceDB
            from ..person.db_services import PersonServiceDB
            from ..player.db_services import PlayerServiceDB
            from ..player_team_tournament.db_services import (
                PlayerTeamTournamentServiceDB,
            )

            parsed_match = await parse_match_and_create_jsons(eesl_match_id)
            match_service = MatchServiceDB(db)
            position_service = PositionServiceDB(db)
            match = await match_service.get_match_by_eesl_id(eesl_match_id)
            team_a = await TeamServiceDB(db).get_team_by_eesl_id(
                parsed_match["team_a_eesl_id"]
            )
            team_b = await TeamServiceDB(db).get_team_by_eesl_id(
                parsed_match["team_b_eesl_id"]
            )

            created_players_match = []

            if parsed_match and match:
                existing_player_ids = set()
                for home_player in parsed_match["roster_a"]:
                    # pprint(home_player)
                    position = await position_service.get_position_by_title(
                        home_player["player_position"]
                    )
                    if position is None:
                        position_schema = {
                            "title": home_player["player_position"],
                            "sport_id": 1,
                        }
                        position = await PositionServiceDB(db).create_new_position(
                            PositionSchemaCreate(**position_schema)
                        )
                    person = await PersonServiceDB(db).get_person_by_eesl_id(
                        home_player["player_eesl_id"]
                    )
                    if person is None:
                        player_in_team = await collect_player_full_data_eesl(
                            home_player["player_eesl_id"]
                        )
                        person_schema = PersonSchemaCreate(**player_in_team["person"])
                        person = await PersonServiceDB(db).create_or_update_person(
                            person_schema
                        )

                    player = await PlayerServiceDB(db).get_player_by_eesl_id(
                        home_player["player_eesl_id"]
                    )
                    if player is None:
                        player_schema = PlayerSchemaCreate(
                            **{
                                "sport_id": 1,
                                "person_id": person.id,
                                "player_eesl_id": home_player["player_eesl_id"],
                            }
                        )
                        player = await PlayerServiceDB(db).create_or_update_player(
                            player_schema
                        )

                    player_in_team = await PlayerTeamTournamentServiceDB(
                        db
                    ).get_player_team_tournament_by_eesl_id(
                        home_player["player_eesl_id"]
                    )

                    if player_in_team is None:
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
                        player_in_team = await PlayerTeamTournamentServiceDB(
                            db
                        ).create_or_update_player_team_tournament(
                            created_player_in_team_schema
                        )

                    if team_a is None or player_in_team is None:
                        continue

                    player_eesl_id = home_player.get("player_eesl_id")
                    if player_eesl_id in existing_player_ids:
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

                    print("eesl_id", player_schema["player_match_eesl_id"])

                    exist_player_in_match = (
                        await self.service.get_player_match_by_eesl_id(
                            player_schema["player_match_eesl_id"]
                        )
                    )

                    if exist_player_in_match:
                        print("Player in matchhhhhhhhhhhh")
                        pprint(exist_player_in_match.__dict__)
                        if exist_player_in_match.is_start:
                            print(
                                "Player in starttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
                            )
                            player_schema[
                                "player_match_eesl_id"
                            ] = exist_player_in_match.player_match_eesl_id
                            player_schema[
                                "player_team_tournament_id"
                            ] = exist_player_in_match.player_team_tournament_id
                            player_schema[
                                "match_position_id"
                            ] = exist_player_in_match.match_position_id
                            player_schema["match_id"] = exist_player_in_match.match_id
                            player_schema[
                                "match_number"
                            ] = exist_player_in_match.match_number
                            player_schema["team_id"] = exist_player_in_match.team_id
                            player_schema["is_start"] = True

                    player = PlayerMatchSchemaCreate(**player_schema)
                    created_player = await self.service.create_or_update_player_match(
                        player
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
                        position_schema = {
                            "title": away_player["player_position"],
                            "sport_id": 1,
                        }
                        position = await PositionServiceDB(db).create_new_position(
                            PositionSchemaCreate(**position_schema)
                        )
                    person = await PersonServiceDB(db).get_person_by_eesl_id(
                        away_player["player_eesl_id"]
                    )
                    if person is None:
                        player_in_team = await collect_player_full_data_eesl(
                            away_player["player_eesl_id"]
                        )
                        person_schema = PersonSchemaCreate(**player_in_team["person"])
                        person = await PersonServiceDB(db).create_or_update_person(
                            person_schema
                        )

                    player = await PlayerServiceDB(db).get_player_by_eesl_id(
                        away_player["player_eesl_id"]
                    )
                    if player is None:
                        player_schema = PlayerSchemaCreate(
                            **{
                                "sport_id": 1,
                                "person_id": person.id,
                                "player_eesl_id": away_player["player_eesl_id"],
                            }
                        )
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
                                    "team_id": team_a.id,
                                    "tournament_id": match.tournament_id,
                                    "player_number": away_player["player_number"],
                                }
                            )
                        )
                        player_in_team = await PlayerTeamTournamentServiceDB(
                            db
                        ).create_or_update_player_team_tournament(
                            created_player_in_team_schema
                        )

                    # player_in_team = await PlayerTeamTournamentServiceDB(db).get_player_team_tournament_by_eesl_id(
                    #     away_player['player_eesl_id'])

                    if team_b is None or player_in_team is None:
                        continue

                    player_eesl_id = away_player.get("player_eesl_id")
                    if player_eesl_id in existing_player_ids:
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

                    print("eesl_id", player_schema["player_match_eesl_id"])

                    exist_player_in_match = (
                        await self.service.get_player_match_by_eesl_id(
                            player_schema["player_match_eesl_id"]
                        )
                    )

                    if exist_player_in_match:
                        print("Player in matchhhhhhhhhhhh")
                        pprint(exist_player_in_match.__dict__)
                        if exist_player_in_match.is_start:
                            print(
                                "Player in starttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt"
                            )
                            player_schema[
                                "player_match_eesl_id"
                            ] = exist_player_in_match.player_match_eesl_id
                            player_schema[
                                "player_team_tournament_id"
                            ] = exist_player_in_match.player_team_tournament_id
                            player_schema[
                                "match_position_id"
                            ] = exist_player_in_match.match_position_id
                            player_schema["match_id"] = exist_player_in_match.match_id
                            player_schema[
                                "match_number"
                            ] = exist_player_in_match.match_number
                            player_schema["team_id"] = exist_player_in_match.team_id
                            player_schema["is_start"] = True

                    player = PlayerMatchSchemaCreate(**player_schema)
                    created_player = await self.service.create_or_update_player_match(
                        player
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

        return router


api_player_match_router = PlayerMatchAPIRouter(PlayerMatchServiceDB(db)).route()
