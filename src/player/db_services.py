from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from src.core.decorators import handle_service_exceptions
from src.core.models import (
    BaseServiceDB,
    PersonDB,
    PlayerDB,
    PlayerTeamTournamentDB,
)
from src.core.models.base import Database
from src.core.schema_helpers import PaginationMetadata

from ..logging_config import get_logger
from .schemas import (
    PaginatedPlayerWithDetailsResponse,
    PlayerSchema,
    PlayerSchemaCreate,
    PlayerSchemaUpdate,
    PlayerWithDetailsSchema,
)

if TYPE_CHECKING:
    from src.core.models import PlayerDB

ITEM = "PLAYER"


class PlayerServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PlayerDB)
        self.logger = get_logger("backend_logger_PlayerServiceDB", self)
        self.logger.debug("Initialized PlayerServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: PlayerSchemaCreate | PlayerSchemaUpdate,
    ) -> PlayerDB:
        self.logger.debug(f"Starting to create PlayerDB with data: {item.__dict__}")
        return await super().create(item)

    async def create_or_update_player(
        self,
        p: PlayerSchemaCreate | PlayerSchemaUpdate,
    ) -> PlayerDB | None:
        return await super().create_or_update(p, eesl_field_name="player_eesl_id")

    async def get_player_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "player_eesl_id",
    ) -> PlayerDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching with person", reraise_not_found=True
    )
    async def get_player_with_person(self, player_id: int) -> PlayerSchema:
        self.logger.debug(f"Get {ITEM} with person data {player_id}")
        player_with_person_data = await self.get_related_item_level_one_by_id(player_id, "person")
        if player_with_person_data:
            self.logger.debug(f"Got {ITEM} with person data {player_with_person_data}")
            return player_with_person_data
        else:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404,
                detail=f"Person does not exist for {ITEM} id:{player_id}",
            )

    async def update(
        self,
        item_id: int,
        item: PlayerSchemaUpdate,
        **kwargs,
    ) -> PlayerDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching players with pagination and details",
        return_value_on_not_found=None,
    )
    async def search_players_with_pagination_details(
        self,
        sport_id: int,
        search_query: str | None = None,
        team_id: int | None = None,
        user_id: int | None = None,
        isprivate: bool | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "second_name",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedPlayerWithDetailsResponse:
        self.logger.debug(
            f"Search players with details: sport_id={sport_id}, query={search_query}, "
            f"team_id={team_id}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = (
                select(PlayerDB)
                .where(PlayerDB.sport_id == sport_id)
                .join(PersonDB, PlayerDB.person_id == PersonDB.id)
                .options(
                    selectinload(PlayerDB.person),
                    selectinload(PlayerDB.player_team_tournament).selectinload(
                        PlayerTeamTournamentDB.team
                    ),
                    selectinload(PlayerDB.player_team_tournament).selectinload(
                        PlayerTeamTournamentDB.position
                    ),
                )
            )

            if user_id is not None:
                base_query = base_query.where(PlayerDB.user_id == user_id)

            if isprivate is not None:
                base_query = base_query.where(PlayerDB.isprivate == isprivate)

            if team_id:
                base_query = base_query.join(
                    PlayerTeamTournamentDB, PlayerDB.id == PlayerTeamTournamentDB.player_id
                ).where(PlayerTeamTournamentDB.team_id == team_id)

            if search_query:
                search_pattern = f"%{search_query}%"
                base_query = base_query.where(
                    (PersonDB.first_name.ilike(search_pattern).collate("en-US-x-icu"))
                    | (PersonDB.second_name.ilike(search_pattern).collate("en-US-x-icu"))
                )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr = PersonDB.second_name.asc() if ascending else PersonDB.second_name.desc()
            data_query = base_query.order_by(order_expr).offset(skip).limit(limit)
            result = await session.execute(data_query)
            players = result.scalars().all()

            players_with_details = []
            for p in players:
                player_team_tournaments_info = []
                for ptt in p.player_team_tournament:
                    player_team_tournaments_info.append(
                        {
                            "id": ptt.id,
                            "player_team_tournament_eesl_id": ptt.player_team_tournament_eesl_id,
                            "player_number": ptt.player_number,
                            "team_id": ptt.team_id,
                            "team_title": ptt.team.title if ptt.team else None,
                            "position_id": ptt.position_id,
                            "position_title": ptt.position.title if ptt.position else None,
                            "tournament_id": ptt.tournament_id,
                        }
                    )

                players_with_details.append(
                    {
                        "id": p.id,
                        "sport_id": p.sport_id,
                        "person_id": p.person_id,
                        "player_eesl_id": p.player_eesl_id,
                        "first_name": p.person.first_name if p.person else None,
                        "second_name": p.person.second_name if p.person else None,
                        "player_team_tournaments": player_team_tournaments_info,
                    }
                )

            return PaginatedPlayerWithDetailsResponse(
                data=[PlayerWithDetailsSchema.model_validate(p) for p in players_with_details],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
