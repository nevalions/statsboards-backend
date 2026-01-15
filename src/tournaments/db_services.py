from sqlalchemy import not_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from src.core.decorators import handle_service_exceptions
from src.core.models import (
    BaseServiceDB,
    MatchDB,
    PlayerDB,
    PlayerTeamTournamentDB,
    SponsorDB,
    SponsorLineDB,
    TeamDB,
    TeamTournamentDB,
    TournamentDB,
)
from src.core.models.base import Database
from src.core.schema_helpers import PaginationMetadata

from ..logging_config import get_logger
from ..player.schemas import (
    PaginatedPlayerWithDetailsResponse,
    PlayerWithDetailsSchema,
)
from ..sponsor_lines.db_services import SponsorLineServiceDB
from .schemas import (
    PaginatedTeamResponse,
    TeamSchema,
    TournamentSchemaCreate,
    TournamentSchemaUpdate,
)

ITEM = "TOURNAMENT"


class TournamentServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            TournamentDB,
        )
        self.logger = get_logger("backend_logger_TournamentServiceDB", self)
        self.logger.debug("Initialized TournamentServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: TournamentSchemaCreate | TournamentSchemaUpdate,
    ) -> TournamentDB:
        self.logger.debug(f"Create new {ITEM}:{item}")
        return await super().create(item)

    async def create_or_update_tournament(
        self,
        t: TournamentSchemaCreate | TournamentSchemaUpdate,
    ) -> TournamentDB:
        return await super().create_or_update(t, eesl_field_name="tournament_eesl_id")

    async def get_tournament_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "tournament_eesl_id",
    ) -> TournamentDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: TournamentSchemaUpdate,
        **kwargs,
    ) -> TournamentDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_teams_by_tournament(
        self,
        tournament_id: int,
    ) -> list[TeamDB]:
        self.logger.debug(f"Get teams by {ITEM} id:{tournament_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(TeamDB)
                .join(TeamTournamentDB, TeamDB.id == TeamTournamentDB.team_id)
                .where(TeamTournamentDB.tournament_id == tournament_id)
                .order_by(TeamDB.title)
            )
            results = await session.execute(stmt)
            teams = results.scalars().all()
            return teams

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching teams in tournament with pagination",
        return_value_on_not_found=None,
    )
    async def get_teams_by_tournament_with_pagination(
        self,
        tournament_id: int,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "title",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedTeamResponse:
        self.logger.debug(
            f"Search teams in tournament id:{tournament_id}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = (
                select(TeamDB)
                .join(TeamTournamentDB, TeamDB.id == TeamTournamentDB.team_id)
                .where(TeamTournamentDB.tournament_id == tournament_id)
            )
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

    # async def get_players_by_tournament(
    #         self,
    #         tournament_id: int,
    # ):
    #     return await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         "players_team_tournament",
    #     )

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching players", return_value_on_not_found=[]
    )
    async def get_players_by_tournament(
        self,
        tournament_id: int,
    ) -> list[PlayerTeamTournamentDB]:
        self.logger.debug(f"Get players by {ITEM} id:{tournament_id}")
        async with self.db.async_session() as session:
            stmt = select(PlayerTeamTournamentDB).where(
                PlayerTeamTournamentDB.tournament_id == tournament_id
            )

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching available players", return_value_on_not_found=[]
    )
    async def get_available_players_for_tournament(
        self,
        tournament_id: int,
    ) -> list[PlayerDB]:
        self.logger.debug(f"Get available players for {ITEM} id:{tournament_id}")
        async with self.db.async_session() as session:
            tournament = await session.get(TournamentDB, tournament_id)
            if not tournament:
                return []

            subquery = select(PlayerTeamTournamentDB.player_id).where(
                PlayerTeamTournamentDB.tournament_id == tournament_id
            )

            stmt = (
                select(PlayerDB)
                .where(PlayerDB.sport_id == tournament.sport_id)
                .options(selectinload(PlayerDB.person))
                .where(not_(PlayerDB.id.in_(subquery.scalar_subquery())))
            )

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching available teams", return_value_on_not_found=[]
    )
    async def get_available_teams_for_tournament(
        self,
        tournament_id: int,
    ) -> list[TeamDB]:
        self.logger.debug(f"Get available teams for {ITEM} id:{tournament_id}")
        async with self.db.async_session() as session:
            tournament = await session.get(TournamentDB, tournament_id)
            if not tournament:
                return []

            subquery = select(TeamTournamentDB.team_id).where(
                TeamTournamentDB.tournament_id == tournament_id
            )

            stmt = (
                select(TeamDB)
                .where(TeamDB.sport_id == tournament.sport_id)
                .where(not_(TeamDB.id.in_(subquery.scalar_subquery())))
                .order_by(TeamDB.title)
            )

            results = await session.execute(stmt)
            teams = results.scalars().all()
            return teams

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching players without team in tournament",
        return_value_on_not_found=None,
    )
    async def get_players_without_team_in_tournament(
        self,
        tournament_id: int,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "second_name",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedPlayerWithDetailsResponse:
        from src.core.models.person import PersonDB

        self.logger.debug(
            f"Get players without team in tournament {tournament_id}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = (
                select(PlayerDB)
                .join(PlayerTeamTournamentDB, PlayerDB.id == PlayerTeamTournamentDB.player_id)
                .join(PersonDB, PlayerDB.person_id == PersonDB.id)
                .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                .where(PlayerTeamTournamentDB.team_id.is_(None))
                .options(selectinload(PlayerDB.person))
            )

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
            order_expr_two = PersonDB.id.asc() if ascending else PersonDB.id.desc()
            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            players = result.scalars().all()

            return PaginatedPlayerWithDetailsResponse(
                data=[
                    PlayerWithDetailsSchema.model_validate(
                        {
                            "id": p.id,
                            "sport_id": p.sport_id,
                            "person_id": p.person_id,
                            "player_eesl_id": p.player_eesl_id,
                            "first_name": p.person.first_name if p.person else None,
                            "second_name": p.person.second_name if p.person else None,
                            "player_team_tournaments": [],
                        }
                    )
                    for p in players
                ],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )

    async def get_count_of_matches_by_tournament(
        self,
        tournament_id: int,
    ) -> int:
        self.logger.debug(f"Get matches by {ITEM} id:{tournament_id}")
        return await self.get_count_of_items_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_matches_by_tournament(
        self,
        tournament_id: int,
    ) -> list[MatchDB]:
        self.logger.debug(f"Get matches by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "matches",
        )

    async def get_matches_by_tournament_with_pagination(
        self,
        tournament_id: int,
        skip: int = 0,
        limit: int = 20,
        order_exp: str = "id",
        order_exp_two: str = "id",
    ) -> list[MatchDB]:
        self.logger.debug(
            f"Get matches by {ITEM} id:{tournament_id} with pagination: skip={skip}, limit={limit}"
        )
        return await self.get_related_item_level_one_by_id(
            tournament_id,
            "matches",
            skip=skip,
            limit=limit,
            order_by=order_exp,
            order_by_two=order_exp_two,
        )

    async def get_main_tournament_sponsor(self, tournament_id: int) -> SponsorDB | None:
        self.logger.debug(f"Get main tournament's sponsor by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(tournament_id, "main_sponsor")

    async def get_tournament_sponsor_line(self, tournament_id: int) -> SponsorLineDB | None:
        self.logger.debug(f"Get tournament's sponsor line by {ITEM} id:{tournament_id}")
        return await self.get_related_item_level_one_by_id(tournament_id, "sponsor_line")

    async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int) -> list[SponsorDB]:
        sponsor_service = SponsorLineServiceDB(self.db)
        self.logger.debug(f"Get sponsors of tournament sponsor line {ITEM} id:{tournament_id}")
        return await self.get_nested_related_item_by_id(
            tournament_id,
            sponsor_service,
            "sponsor_line",
            "sponsors",
        )

    # async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
    #     sponsor_line = await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         'sponsor_line'
    #     )
    #
    #     if sponsor_line is not None:
    #         sponsor_line_id = sponsor_line.id
    #         sponsor_service = SponsorLineServiceDB(self.db)
    #         sponsors = await sponsor_service.get_related_items_level_one_by_id(
    #             sponsor_line_id,
    #             'sponsors'
    #         )
    #         return sponsors
    #
    #     return []

    # async def get_sponsors_of_tournament_sponsor_line(self, tournament_id: int):
    #     return await self.get_related_items_level_one_by_id(
    #         tournament_id,
    #         'sponsor_line',
    #         'sponsors'
    #     )
