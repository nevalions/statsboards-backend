from typing import Annotated

from fastapi import HTTPException, Query

from src.core import BaseRouter, db
from src.pars_eesl.pars_all_players_from_eesl import (
    parse_all_players_from_eesl_index_page_eesl,
)
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate

from ..logging_config import get_logger
from .db_services import PlayerServiceDB
from .schemas import (
    PaginatedPlayerWithDetailsResponse,
    PlayerSchema,
    PlayerSchemaCreate,
    PlayerSchemaUpdate,
)


class PlayerAPIRouter(BaseRouter[PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate]):
    def __init__(self, service: PlayerServiceDB):
        super().__init__("/api/players", ["players"], service)
        self.logger = get_logger("backend_logger_PlayerAPIRouter", self)
        self.logger.debug("Initialized PlayerAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=PlayerSchema,
        )
        async def create_player_endpoint(
            player: PlayerSchemaCreate,
        ):
            self.logger.debug(f"Create or update player endpoint got data: {player}")
            new_player = await self.service.create_or_update_player(player)
            if new_player:
                return PlayerSchema.model_validate(new_player)
            else:
                self.logger.error(f"Error on create or update player, got data: {player}")
                raise HTTPException(status_code=409, detail=f"Player creation fail {player}")

        @router.get("/eesl_id/{eesl_id}", response_model=PlayerSchema)
        async def get_player_by_eesl_id_endpoint(
            eesl_id: int,
        ):
            self.logger.debug(f"Get player by eesl_id: {eesl_id} endpoint")
            player = await self.service.get_player_by_eesl_id(value=eesl_id)
            if player is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Player eesl_id({eesl_id}) not found",
                )
            return PlayerSchema.model_validate(player)

        @router.put(
            "/{item_id}/",
            response_model=PlayerSchema,
        )
        async def update_player_endpoint(
            item_id: int,
            item: PlayerSchemaUpdate,
        ):
            try:
                self.logger.debug(f"Update player endpoint got data: {item}")
                update_ = await self.service.update(item_id, item)
                if update_ is None:
                    raise HTTPException(status_code=404, detail=f"Player id {item_id} not found")
                return PlayerSchema.model_validate(update_)
            except Exception as ex:
                self.logger.error(f"Error on update player: {item} {ex}", exc_info=True)
                raise

        @router.get("/id/{player_id}/person")
        async def person_by_player_id(player_id: int):
            self.logger.debug(f"Get person by player id: {player_id} endpoint")
            try:
                return await self.service.get_player_with_person(player_id)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting person by player id:{player_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching person by player id",
                )

        @router.get(
            "/pars/all_eesl",
        )
        async def get_parse_player_with_person_endpoint():
            self.logger.debug("Get parsed players with person endpoint limit 2 and season 8")
            return await parse_all_players_from_eesl_index_page_eesl(
                start_page=0, limit=2, season_id=8
            )

        @router.get(
            "/paginated/details",
            response_model=PaginatedPlayerWithDetailsResponse,
        )
        async def get_players_paginated_details_endpoint(
            sport_id: Annotated[int, Query(description="Sport ID filter")],
            team_id: Annotated[int | None, Query(description="Team ID filter")] = None,
            page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
            items_per_page: Annotated[
                int, Query(ge=1, le=100, description="Items per page (max 100)")
            ] = 20,
            ascending: Annotated[
                bool, Query(description="Sort order (true=asc, false=desc)")
            ] = True,
            search: Annotated[
                str | None, Query(description="Search query for person names")
            ] = None,
            user_id: Annotated[int | None, Query(description="Filter by user_id")] = None,
            isprivate: Annotated[
                bool | None, Query(description="Filter by isprivate status")
            ] = None,
        ):
            self.logger.debug(
                f"Get players paginated with details: sport_id={sport_id}, team_id={team_id}, "
                f"page={page}, items_per_page={items_per_page}, ascending={ascending}, search={search}, "
                f"user_id={user_id}, isprivate={isprivate}"
            )
            skip = (page - 1) * items_per_page
            response = await self.service.search_players_with_pagination_details(
                sport_id=sport_id,
                team_id=team_id,
                search_query=search,
                user_id=user_id,
                isprivate=isprivate,
                skip=skip,
                limit=items_per_page,
                ascending=ascending,
            )
            return response

        @router.post("/pars_and_create/all_eesl/start_page/{start_page}/season_id/{season_id}/")
        async def create_parsed_players_with_person_endpoint(
            start_page: int = 0, season_id: int = 8
        ):
            try:
                self.logger.debug("Create parsed players with person from all eesl endpoint")
                players = await parse_all_players_from_eesl_index_page_eesl(
                    start_page=start_page, limit=None, season_id=season_id
                )
                created_persons = []
                created_players = []

                if players:
                    for player_with_person in players:
                        person = PersonSchemaCreate(**player_with_person["person"])
                        created_person = await PersonServiceDB(db).create_or_update_person(person)
                        created_persons.append(created_person)
                        if created_person:
                            self.logger.debug(f"Person created successfully: {created_person}")
                            player_data_dict = player_with_person["player"]
                            player_data_dict["person_id"] = created_person.id
                            player = PlayerSchemaCreate(**player_data_dict)
                            created_player = await self.service.create_or_update_player(player)
                            created_players.append(created_player)
                            self.logger.debug(f"Player created successfully: {created_player}")
                    self.logger.debug(f"Created parsed persons number:{len(created_persons)}")
                    self.logger.debug(f"Created parsed players number:{len(created_players)}")
                    return created_players, created_persons
                else:
                    return []
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error on create parsed players with person from all eesl: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error creating parsed players with person from EESL",
                )

        return router


api_player_router = PlayerAPIRouter(PlayerServiceDB(db)).route()
