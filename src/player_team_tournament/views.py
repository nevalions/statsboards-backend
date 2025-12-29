from typing import List

from fastapi import HTTPException

from src.core import BaseRouter, db

from ..logging_config import get_logger, setup_logging
from ..pars_eesl.pars_all_players_from_eesl import collect_player_full_data_eesl
from ..pars_eesl.parse_player_team_tournament import (
    parse_players_from_team_tournament_eesl_and_create_jsons,
)
from ..person.db_services import PersonServiceDB
from ..person.schemas import PersonSchema, PersonSchemaCreate
from ..player.db_services import PlayerServiceDB
from ..player.schemas import PlayerSchemaCreate
from ..positions.db_services import PositionServiceDB
from ..positions.schemas import PositionSchemaCreate
from ..teams.db_services import TeamServiceDB
from ..tournaments.db_services import TournamentServiceDB
from .db_services import PlayerTeamTournamentServiceDB
from .schemas import (
    PlayerTeamTournamentSchema,
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
)

setup_logging()


class PlayerTeamTournamentAPIRouter(
    BaseRouter[
        PlayerTeamTournamentSchema,
        PlayerTeamTournamentSchemaCreate,
        PlayerTeamTournamentSchemaUpdate,
    ]
):
    def __init__(self, service: PlayerTeamTournamentServiceDB):
        super().__init__(
            "/api/players_team_tournament", ["players_team_tournament"], service
        )
        self.logger = get_logger("backend_logger_PlayerTeamTournamentAPIRouter", self)
        self.logger.debug("Initialized PlayerTeamTournamentAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def create_player_team_tournament_endpoint(
            player_team_tournament: PlayerTeamTournamentSchemaCreate,
        ):
            try:
                self.logger.debug(
                    f"Create or update player_team_tournament endpoint got data {player_team_tournament}"
                )
                new_player_team_tournament = (
                    await self.service.create_or_update_player_team_tournament(
                        player_team_tournament
                    )
                )
                if new_player_team_tournament:
                    return PlayerTeamTournamentSchema.model_validate(new_player_team_tournament)
                else:
                    raise HTTPException(
                        status_code=409, detail="Player_team_tournament creation fail"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error creating player_team_tournament with data {player_team_tournament} {e}",
                    exc_info=True,
                )

        @router.get(
            "/eesl_id/{eesl_id}",
            response_model=PlayerTeamTournamentSchema,
        )
        async def get_player_team_tournament_by_eesl_id_endpoint(
            eesl_id: int,
        ):
            try:
                self.logger.debug(
                    f"Getting player_team_tournament endpoint by eesl_id {eesl_id}"
                )
                tournament = await self.service.get_player_team_tournament_by_eesl_id(
                    value=eesl_id
                )
                if tournament is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"player_team_tournament by eesl_id({eesl_id}) not found",
                    )
                return PlayerTeamTournamentSchema.model_validate(tournament)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(
                    f"Error getting player_team_tournament by eesl_id {eesl_id} {e}",
                    exc_info=True,
                )

        @router.put(
            "/{item_id}/",
            response_model=PlayerTeamTournamentSchema,
        )
        async def update_player_team_tournament_endpoint(
            item_id: int,
            item: PlayerTeamTournamentSchemaUpdate,
        ):
            try:
                self.logger.debug(
                    f"Update player_team_tournament endpoint got data {item}"
                )
                update_ = await self.service.update(
                    item_id, item
                )
                if update_ is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Player team tournament id {item_id} not found",
                    )
                return PlayerTeamTournamentSchema.model_validate(update_)
            except Exception as e:
                self.logger.error(
                    f"Error updating player_team_tournament with data {item_id} {e}",
                    exc_info=True,
                )

        # @router.get(
        #     "/tournament/{tournament_id}/players",
        #     # response_model=List[PlayerTeamTournamentSchema],
        # )
        # async def get_all_players_by_tournament_endpoint(tournament_id: int):
        #     return await self.service.get_all_players_by_tournament(tournament_id)

        @router.get(
            "/id/{player_id}/person/",
            response_model=PersonSchema,
        )
        async def get_player_team_tournament_with_person_endpoint(player_id: int):
            return await self.service.get_player_team_tournament_with_person(player_id)

        @router.get(
            "/pars/tournament/{tournament_id}/team/{team_id}",
        )
        async def get_parse_player_to_team_tournament_endpoint(
            tournament_id: int, team_id: int
        ):
            self.logger.debug("Get parse_player_to_team_tournament endpoint")
            return await parse_players_from_team_tournament_eesl_and_create_jsons(
                tournament_id, team_id
            )

        @router.put(
            "/pars_and_create/tournament/{tournament_id}/team/id/{team_id}/players",
            response_model=List[PlayerTeamTournamentSchema],
        )
        async def create_parsed_players_to_team_tournament_endpoint(
            tournament_id: int, team_id: int
        ):
            try:
                self.logger.debug(
                    f"Star parsing players from team id:{team_id} tournament id:{tournament_id}"
                )
                players_from_team_tournament = (
                    await parse_players_from_team_tournament_eesl_and_create_jsons(
                        tournament_id,
                        team_id,
                    )
                )

                created_persons = []
                created_players = []
                created_players_in_team_tournament = []
                if players_from_team_tournament:
                    for ptt in players_from_team_tournament:
                        player_in_team = await collect_player_full_data_eesl(
                            ptt["player_eesl_id"]
                        )

                        person = PersonSchemaCreate(**player_in_team["person"])
                        created_person = await PersonServiceDB(
                            db
                        ).create_or_update_person(person)
                        # pprint(created_person.__dict__)
                        created_persons.append(created_person)
                        if created_person:
                            player_data_dict = player_in_team["player"]
                            player_data_dict["person_id"] = created_person.id
                            # pprint(player_data_dict)
                            player = PlayerSchemaCreate(**player_data_dict)
                            created_player = await PlayerServiceDB(
                                db
                            ).create_or_update_player(player)
                            # pprint(created_player.__dict__)
                            created_players.append(created_player)

                            tournament = await TournamentServiceDB(
                                db
                            ).get_tournament_by_eesl_id(ptt["eesl_tournament_id"])
                            team = await TeamServiceDB(db).get_team_by_eesl_id(
                                ptt["eesl_team_id"]
                            )
                            position = await PositionServiceDB(
                                db
                            ).get_position_by_title(ptt["player_position"])
                            if not position:
                                new_position = PositionSchemaCreate(
                                    **{"title": ptt["player_position"], "sport_id": 1}
                                )
                                new_position_created = await PositionServiceDB(
                                    db
                                ).create(new_position)
                                if ptt and team and tournament:
                                    p = {
                                        "player_team_tournament_eesl_id": ptt[
                                            "player_eesl_id"
                                        ],
                                        "player_id": created_player.id,
                                        "position_id": new_position_created.id,
                                        "team_id": team.id,
                                        "tournament_id": tournament.id,
                                        "player_number": ptt["player_number"],
                                    }
                                    created_player_in_team_dict = (
                                        PlayerTeamTournamentSchemaCreate(**p)
                                    )
                                    created_player_in_team = await self.service.create_or_update_player_team_tournament(
                                        created_player_in_team_dict
                                    )
                                    created_players_in_team_tournament.append(
                                        created_player_in_team
                                    )
                                    self.logger.info(
                                        f"Created player in team tournament with position: {created_player_in_team}"
                                    )
                            else:
                                if ptt and team and tournament:
                                    # print('with position')
                                    p = {
                                        "player_team_tournament_eesl_id": ptt[
                                            "player_eesl_id"
                                        ],
                                        "player_id": created_player.id,
                                        "position_id": position.id,
                                        "team_id": team.id,
                                        "tournament_id": tournament.id,
                                        "player_number": ptt["player_number"],
                                    }
                                    created_player_in_team_dict = (
                                        PlayerTeamTournamentSchemaCreate(**p)
                                    )
                                    created_player_in_team = await self.service.create_or_update_player_team_tournament(
                                        created_player_in_team_dict
                                    )
                                    created_players_in_team_tournament.append(
                                        created_player_in_team
                                    )

                                    self.logger.info(
                                        f"Created player in team tournament without position: {created_player_in_team}"
                                    )

                    return created_players_in_team_tournament
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No players in team id:{team_id} tournament id:{tournament_id}",
                    )
            except Exception as e:
                self.logger.error(
                    f"Error parsing player in team id:{team_id} tournament id:{tournament_id} : {e}",
                    exc_info=True,
                )

        return router


api_player_team_tournament_router = PlayerTeamTournamentAPIRouter(
    PlayerTeamTournamentServiceDB(db)
).route()
