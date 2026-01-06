
from sqlalchemy import select
from sqlalchemy.sql import func

from src.core.models import (
    BaseServiceDB,
    MatchDB,
    PlayerTeamTournamentDB,
    TeamDB,
    handle_service_exceptions,
)
from src.core.models.base import Database
from src.core.schema_helpers import PaginationMetadata
from src.positions.db_services import PositionServiceDB

from ..logging_config import get_logger
from .schemas import (
    PaginatedTeamResponse,
    TeamSchema,
    TeamSchemaCreate,
    TeamSchemaUpdate,
)

ITEM = "TEAM"


class TeamServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, TeamDB)
        self.logger = get_logger("backend_logger_TeamServiceDB", self)
        self.logger.debug("Initialized TeamServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: TeamSchemaCreate | TeamSchemaUpdate,
    ) -> TeamDB:
        return await super().create(item)

    async def create_or_update_team(
        self,
        t: TeamSchemaCreate | TeamSchemaUpdate,
    ) -> TeamDB:
        return await super().create_or_update(t, eesl_field_name="team_eesl_id")

    async def get_team_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "team_eesl_id",
    ) -> TeamDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def get_matches_by_team_id(
        self,
        team_id: int,
    ) -> list[MatchDB]:
        self.logger.debug(f"Get matches by {ITEM} id:{team_id}")
        return await self.get_related_item_level_one_by_id(
            team_id,
            "matches",
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting players by team_id_tournament_id",
        return_value_on_not_found=[],
    )
    async def get_players_by_team_id_tournament_id(
        self,
        team_id: int,
        tournament_id: int,
    ) -> list[PlayerTeamTournamentDB]:
        self.logger.debug(f"Get players by {ITEM} id:{team_id} and tournament id:{tournament_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(PlayerTeamTournamentDB)
                .where(PlayerTeamTournamentDB.team_id == team_id)
                .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
            )

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting players with person by team_id_tournament_id",
        return_value_on_not_found=[],
    )
    async def get_players_by_team_id_tournament_id_with_person(
        self,
        team_id: int,
        tournament_id: int,
    ) -> list[dict]:
        self.logger.debug(
            f"Get players with person by {ITEM} id:{team_id} and tournament id:{tournament_id}"
        )
        from src.player_team_tournament.db_services import (
            PlayerTeamTournamentServiceDB,
        )

        player_service = PlayerTeamTournamentServiceDB(self.db)
        position_service = PositionServiceDB(self.db)
        players = await self.get_players_by_team_id_tournament_id(team_id, tournament_id)

        players_full_data = []
        if players:
            for p in players:
                person = await player_service.get_player_team_tournament_with_person(p.id)
                position = await position_service.get_by_id(p.position_id)
                # players_full_data.append(person)
                # players_full_data.append(p)
                player_full_data = {
                    "player_team_tournament": p,
                    "person": person,
                    "position": position,
                }
                players_full_data.append(player_full_data)
        return players_full_data

    async def update(
        self,
        item_id: int,
        item: TeamSchemaUpdate,
        **kwargs,
    ) -> TeamDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching teams with pagination",
        return_value_on_not_found=None,
    )
    async def search_teams_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "title",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedTeamResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = select(TeamDB)
            base_query = await self._apply_search_filters(
                base_query,
                [(TeamDB, "title")],
                search_query,
            )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                TeamDB, order_by, order_by_two, ascending, TeamDB.title, TeamDB.id
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            teams = result.scalars().all()

            return PaginatedTeamResponse(
                data=[TeamSchema.model_validate(t) for t in teams],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
