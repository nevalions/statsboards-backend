from typing import Annotated

from fastapi import Depends, HTTPException, Query

from src.core import BaseRouter
from src.core.dependencies import PersonService, PlayerService
from src.core.models import handle_view_exceptions
from src.pars_eesl.pars_all_players_from_eesl import (
    parse_all_players_from_eesl_index_page_eesl,
)

from ..logging_config import get_logger
from .db_services import PlayerServiceDB
from .schemas import (
    PaginatedPlayerWithDetailsAndPhotosResponse,
    PaginatedPlayerWithDetailsResponse,
    PaginatedPlayerWithFullDetailsResponse,
    PlayerAddToSportSchema,
    PlayerCareerResponseSchema,
    PlayerDetailInTournamentResponse,
    PlayerSchema,
    PlayerSchemaCreate,
    PlayerSchemaUpdate,
)


class PlayerAPIRouter(BaseRouter[PlayerSchema, PlayerSchemaCreate, PlayerSchemaUpdate]):
    def __init__(self, service: PlayerServiceDB | None = None, service_name: str | None = None):
        super().__init__("/api/players", ["players"], service, service_name=service_name)
        self.logger = get_logger("PlayerAPIRouter", self)
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
            new_player = await self.loaded_service.create_or_update_player(player)
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
            player = await self.loaded_service.get_player_by_eesl_id(value=eesl_id)
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
                update_ = await self.loaded_service.update(item_id, item)
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
                return await self.loaded_service.get_player_with_person(player_id)
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
                ) from ex

        @router.get("/id/{player_id}/career", response_model=PlayerCareerResponseSchema)
        async def player_career_endpoint(player_id: int):
            self.logger.debug(f"Get player career for player_id:{player_id} endpoint")
            try:
                return await self.loaded_service.get_player_career(player_id)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting player career for player_id:{player_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching player career",
                ) from ex

        @router.get(
            "/id/{player_id}/in-tournament/{tournament_id}",
            response_model=PlayerDetailInTournamentResponse,
        )
        async def player_detail_in_tournament_endpoint(player_id: int, tournament_id: int):
            self.logger.debug(
                f"Get player {player_id} detail in tournament {tournament_id} endpoint"
            )
            try:
                return await self.loaded_service.get_player_detail_in_tournament(
                    player_id, tournament_id
                )
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error getting player {player_id} detail in tournament {tournament_id} {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error fetching player detail in tournament",
                ) from ex

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
            response = await self.loaded_service.search_players_with_pagination_details(
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

        @router.get(
            "/paginated/details-with-photos",
            response_model=PaginatedPlayerWithDetailsAndPhotosResponse,
        )
        async def get_players_paginated_details_with_photos_endpoint(
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
                f"Get players paginated with details and photos: sport_id={sport_id}, team_id={team_id}, "
                f"page={page}, items_per_page={items_per_page}, ascending={ascending}, search={search}, "
                f"user_id={user_id}, isprivate={isprivate}"
            )
            skip = (page - 1) * items_per_page
            response = await self.loaded_service.search_players_with_pagination_details_and_photos(
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

        @router.get(
            "/paginated/full-details",
            response_model=PaginatedPlayerWithFullDetailsResponse,
        )
        async def get_players_paginated_full_details_endpoint(
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
                f"Get players paginated with full details: sport_id={sport_id}, team_id={team_id}, "
                f"page={page}, items_per_page={items_per_page}, ascending={ascending}, search={search}, "
                f"user_id={user_id}, isprivate={isprivate}"
            )
            skip = (page - 1) * items_per_page
            response = await self.loaded_service.search_players_with_pagination_full_details(
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

        @router.post("/add-person-to-sport", response_model=PlayerSchema)
        async def add_person_to_sport_endpoint(
            data: PlayerAddToSportSchema,
        ):
            self.logger.debug(
                f"Add person to sport: person_id={data.person_id}, sport_id={data.sport_id}"
            )
            try:
                player = await self.loaded_service.add_person_to_sport(
                    person_id=data.person_id,
                    sport_id=data.sport_id,
                    isprivate=data.isprivate,
                    user_id=data.user_id,
                )
                return PlayerSchema.model_validate(player)
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error adding person {data.person_id} to sport {data.sport_id}: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error adding person to sport",
                ) from ex

        @router.delete("/remove-person-from-sport/personid/{person_id}/sportid/{sport_id}")
        async def remove_person_from_sport_endpoint(
            person_id: int,
            sport_id: int,
        ):
            self.logger.debug(f"Remove person {person_id} from sport {sport_id}")
            try:
                success = await self.loaded_service.remove_person_from_sport(
                    person_id=person_id,
                    sport_id=sport_id,
                )
                return {"success": success, "message": "Player removed from sport"}
            except HTTPException:
                raise
            except Exception as ex:
                self.logger.error(
                    f"Error removing person {person_id} from sport {sport_id}: {ex}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error removing person from sport",
                ) from ex

        @router.post("/pars_and_create/all_eesl/start_page/{start_page}/season_id/{season_id}/")
        async def create_parsed_players_with_person_endpoint(
            person_service: PersonService, start_page: int = 0, season_id: int = 8
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
                        created_person = await person_service.create_or_update_person(person)
                        created_persons.append(created_person)
                        if created_person:
                            self.logger.debug(f"Person created successfully: {created_person}")
                            player_data_dict = player_with_person["player"]
                            player_data_dict["person_id"] = created_person.id
                            player = PlayerSchemaCreate(**player_data_dict)
                            created_player = await self.loaded_service.create_or_update_player(
                                player
                            )
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
                ) from ex

        return router


api_player_router = PlayerAPIRouter().route()
