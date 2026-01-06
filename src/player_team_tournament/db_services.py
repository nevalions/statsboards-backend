from math import ceil

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from src.core.models import (
    BaseServiceDB,
    PersonDB,
    PlayerDB,
    PlayerTeamTournamentDB,
    PositionDB,
    TeamDB,
    handle_service_exceptions,
)
from src.core.models.base import Database
from src.player.db_services import PlayerServiceDB

from ..logging_config import get_logger
from .schemas import (
    PaginatedPlayerTeamTournamentResponse,
    PaginatedPlayerTeamTournamentWithDetailsResponse,
    PaginationMetadata,
    PlayerTeamTournamentSchema,
    PlayerTeamTournamentSchemaCreate,
    PlayerTeamTournamentSchemaUpdate,
    PlayerTeamTournamentWithDetailsSchema,
)

ITEM = "PLAYER_TEAM_TOURNAMENT"


class PlayerTeamTournamentServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PlayerTeamTournamentDB)
        self.logger = get_logger("backend_logger_PlayerTeamTournamentServiceDB")
        self.logger.debug("Initialized PlayerTeamTournamentServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: PlayerTeamTournamentSchemaCreate | PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB:
        self.logger.debug(f"Starting to create PlayerTeamTournamentDB with data: {item.__dict__}")
        return await super().create(item)

    @handle_service_exceptions(
        item_name=ITEM, operation="creating or updating", return_value_on_not_found=None
    )
    async def create_or_update_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate | PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB | None:
        self.logger.debug(f"Creat or update {ITEM}:{p}")
        if p.player_team_tournament_eesl_id:
            self.logger.debug(f"Get {ITEM} by eesl id")
            player_team_tournament_from_db = await self.get_player_team_tournament_by_eesl_id(
                p.player_team_tournament_eesl_id
            )
            if player_team_tournament_from_db:
                self.logger.debug(f"{ITEM} exist, updating...")
                return await self.update_player_team_tournament_by_eesl(
                    "player_team_tournament_eesl_id",
                    PlayerTeamTournamentSchemaUpdate(**p.model_dump()),
                )
            else:
                self.logger.debug(f"{ITEM} does not exist, creating...")
                return await self.create_new_player_team_tournament(
                    PlayerTeamTournamentSchemaCreate(**p.model_dump()),
                )
        else:
            if p.tournament_id and p.player_id:
                self.logger.debug(f"Got {ITEM} by player id and tournament id")
                player_team_tournament_from_db = (
                    await self.get_player_team_tournaments_by_tournament_id(
                        p.tournament_id, p.player_id
                    )
                )
                if player_team_tournament_from_db:
                    self.logger.debug(f"{ITEM} exist, updating...")
                    return await self.update(
                        player_team_tournament_from_db.id,
                        PlayerTeamTournamentSchemaUpdate(**p.model_dump()),
                    )
            self.logger.debug(f"{ITEM} does not exist, creating...")
            return await self.create_new_player_team_tournament(
                PlayerTeamTournamentSchemaCreate(**p.model_dump()),
            )

    @handle_service_exceptions(
        item_name=ITEM, operation="updating by eesl ID", return_value_on_not_found=None
    )
    async def update_player_team_tournament_by_eesl(
        self,
        eesl_field_name: str,
        p: PlayerTeamTournamentSchemaUpdate,
    ) -> PlayerTeamTournamentDB | None:
        self.logger.debug(f"Update {ITEM} by {eesl_field_name} {p}")
        if p.player_team_tournament_eesl_id is not None and isinstance(
            p.player_team_tournament_eesl_id, int
        ):
            return await self.update_item_by_eesl_id(
                eesl_field_name,
                p.player_team_tournament_eesl_id,
                p,
            )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid player team tournament {eesl_field_name}",
        )

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create_new_player_team_tournament(
        self,
        p: PlayerTeamTournamentSchemaCreate,
    ) -> PlayerTeamTournamentDB:
        self.logger.debug(f"Create {ITEM} wit data {p}")
        return await super().create(p)

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching by eesl ID", return_value_on_not_found=None
    )
    async def get_player_team_tournament_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "player_team_tournament_eesl_id",
    ) -> PlayerTeamTournamentDB | None:
        self.logger.debug(f"Get {ITEM} by {field_name}: {value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching by tournament and player IDs",
        return_value_on_not_found=None,
    )
    async def get_player_team_tournaments_by_tournament_id(
        self, tournament_id: int, player_id: int
    ) -> PlayerTeamTournamentDB | None:
        self.logger.debug(f"Get {ITEM} by tournament id:{tournament_id} and player id:{player_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(PlayerTeamTournamentDB)
                .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                .where(PlayerTeamTournamentDB.player_id == player_id)
            )

            results = await session.execute(stmt)
            player = results.scalars().one_or_none()
            if player:
                return player
            else:
                return None

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching with person", return_value_on_not_found=None
    )
    async def get_player_team_tournament_with_person(self, player_id: int) -> PlayerDB | None:
        player_service = PlayerServiceDB(self.db)
        return await self.get_nested_related_item_by_id(
            player_id,
            player_service,
            "player",
            "person",
        )

    async def update(
        self,
        item_id: int,
        item: PlayerTeamTournamentSchemaUpdate,
        **kwargs,
    ) -> PlayerTeamTournamentDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(item_name="team rosters for match", operation="fetching")
    async def get_team_rosters_for_match(
        self,
        match_id: int,
        include_available: bool = True,
        include_match_players: bool = True,
    ) -> dict | None:
        """Get all rosters for a match: home, away, available."""
        from src.core.models.match import MatchDB
        from src.core.models.player import PlayerDB
        from src.core.models.player_match import PlayerMatchDB

        self.logger.debug(
            f"Get team rosters for match_id:{match_id} include_available:{include_available} include_match_players:{include_match_players}"
        )

        async with self.db.async_session() as session:
            stmt_match = (
                select(MatchDB)
                .where(MatchDB.id == match_id)
                .options(
                    selectinload(MatchDB.tournaments),
                )
            )
            result_match = await session.execute(stmt_match)
            match = result_match.scalar_one_or_none()

            if not match:
                return None

            result = {
                "match_id": match_id,
                "home_roster": [],
                "away_roster": [],
                "available_home": [],
                "available_away": [],
            }

            if include_match_players:
                home_roster_stmt = (
                    select(PlayerMatchDB)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(PlayerMatchDB.team_id == match.team_a_id)
                    .options(
                        selectinload(PlayerMatchDB.player_team_tournament)
                        .selectinload(PlayerTeamTournamentDB.player)
                        .selectinload(PlayerDB.person),
                        selectinload(PlayerMatchDB.team),
                        selectinload(PlayerMatchDB.match_position),
                    )
                )
                home_roster_result = await session.execute(home_roster_stmt)
                home_roster_players = home_roster_result.scalars().all()

                for pm in home_roster_players:
                    result["home_roster"].append(
                        {
                            "id": pm.id,
                            "player_id": (
                                pm.player_team_tournament.player_id
                                if pm.player_team_tournament
                                else None
                            ),
                            "player": (
                                pm.player_team_tournament.player.__dict__
                                if pm.player_team_tournament and pm.player_team_tournament.player
                                else None
                            ),
                            "team": (
                                {
                                    **pm.team.__dict__,
                                    "logo_url": pm.team.logo_url
                                    if hasattr(pm.team, "logo_url")
                                    else None,
                                }
                                if pm.team
                                else None
                            ),
                            "tournament": (
                                match.tournaments.__dict__ if match.tournaments else None
                            ),
                            "player_number": (
                                pm.player_team_tournament.player_number
                                if pm.player_team_tournament
                                else None
                            ),
                            "is_home_team": True,
                            "is_starting": pm.is_starting,
                            "starting_type": pm.starting_type,
                        }
                    )

                away_roster_stmt = (
                    select(PlayerMatchDB)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(PlayerMatchDB.team_id == match.team_b_id)
                    .options(
                        selectinload(PlayerMatchDB.player_team_tournament)
                        .selectinload(PlayerTeamTournamentDB.player)
                        .selectinload(PlayerDB.person),
                        selectinload(PlayerMatchDB.team),
                        selectinload(PlayerMatchDB.match_position),
                    )
                )
                away_roster_result = await session.execute(away_roster_stmt)
                away_roster_players = away_roster_result.scalars().all()

                for pm in away_roster_players:
                    result["away_roster"].append(
                        {
                            "id": pm.id,
                            "player_id": (
                                pm.player_team_tournament.player_id
                                if pm.player_team_tournament
                                else None
                            ),
                            "player": (
                                pm.player_team_tournament.player.__dict__
                                if pm.player_team_tournament and pm.player_team_tournament.player
                                else None
                            ),
                            "team": (
                                {
                                    **pm.team.__dict__,
                                    "logo_url": pm.team.logo_url
                                    if hasattr(pm.team, "logo_url")
                                    else None,
                                }
                                if pm.team
                                else None
                            ),
                            "tournament": (
                                match.tournaments.__dict__ if match.tournaments else None
                            ),
                            "player_number": (
                                pm.player_team_tournament.player_number
                                if pm.player_team_tournament
                                else None
                            ),
                            "is_home_team": False,
                            "is_starting": pm.is_starting,
                            "starting_type": pm.starting_type,
                        }
                    )

            if include_available:
                subquery_home = (
                    select(PlayerMatchDB.player_team_tournament_id)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(PlayerMatchDB.team_id == match.team_a_id)
                )

                home_available_stmt = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.team_id == match.team_a_id)
                    .where(PlayerTeamTournamentDB.tournament_id == match.tournament_id)
                    .where(~PlayerTeamTournamentDB.id.in_(subquery_home))
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.tournament),
                    )
                )
                home_available_result = await session.execute(home_available_stmt)
                home_available_players = home_available_result.scalars().all()

                for pt in home_available_players:
                    result["available_home"].append(
                        {
                            "id": pt.id,
                            "player_id": pt.player_id,
                            "player": (pt.player.__dict__ if pt.player else None),
                            "team": (
                                {
                                    **pt.team.__dict__,
                                    "logo_url": pt.team.logo_url
                                    if hasattr(pt.team, "logo_url")
                                    else None,
                                }
                                if pt.team
                                else None
                            ),
                            "tournament": (pt.tournament.__dict__ if pt.tournament else None),
                            "player_number": pt.player_number,
                        }
                    )

                subquery_away = (
                    select(PlayerMatchDB.player_team_tournament_id)
                    .where(PlayerMatchDB.match_id == match_id)
                    .where(PlayerMatchDB.team_id == match.team_b_id)
                )

                away_available_stmt = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.team_id == match.team_b_id)
                    .where(PlayerTeamTournamentDB.tournament_id == match.tournament_id)
                    .where(~PlayerTeamTournamentDB.id.in_(subquery_away))
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.tournament),
                    )
                )
                away_available_result = await session.execute(away_available_stmt)
                away_available_players = away_available_result.scalars().all()

                for pt in away_available_players:
                    result["available_away"].append(
                        {
                            "id": pt.id,
                            "player_id": pt.player_id,
                            "player": (pt.player.__dict__ if pt.player else None),
                            "team": (
                                {
                                    **pt.team.__dict__,
                                    "logo_url": pt.team.logo_url
                                    if hasattr(pt.team, "logo_url")
                                    else None,
                                }
                                if pt.team
                                else None
                            ),
                            "tournament": (pt.tournament.__dict__ if pt.tournament else None),
                            "player_number": pt.player_number,
                        }
                    )

            return result

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching tournament players with pagination",
        return_value_on_not_found=None,
    )
    async def search_tournament_players_with_pagination(
        self,
        tournament_id: int,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "player_number",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedPlayerTeamTournamentResponse:
        self.logger.debug(
            f"Search tournament players: tournament_id={tournament_id}, query={search_query}, "
            f"skip={skip}, limit={limit}, order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            if search_query:
                search_pattern = f"%{search_query}%"
                base_query = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                    .join(PlayerDB, PlayerTeamTournamentDB.player_id == PlayerDB.id)
                    .join(PersonDB, PlayerDB.person_id == PersonDB.id)
                    .join(TeamDB, PlayerTeamTournamentDB.team_id == TeamDB.id)
                    .outerjoin(PositionDB, PlayerTeamTournamentDB.position_id == PositionDB.id)
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.position),
                    )
                    .where(
                        PlayerTeamTournamentDB.player_number.ilike(search_pattern)
                        | PersonDB.first_name.ilike(search_pattern).collate("en-US-x-icu")
                        | PersonDB.second_name.ilike(search_pattern).collate("en-US-x-icu")
                        | TeamDB.title.ilike(search_pattern).collate("en-US-x-icu")
                    )
                    .distinct()
                )
            else:
                base_query = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.position),
                    )
                )

            count_stmt = select(func.count(func.distinct(PlayerTeamTournamentDB.id))).select_from(
                base_query
            )
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            total_pages = ceil(total_items / limit) if limit > 0 else 0

            try:
                order_column = getattr(
                    PlayerTeamTournamentDB, order_by, PlayerTeamTournamentDB.player_number
                )
            except AttributeError:
                self.logger.warning(
                    f"Order column {order_by} not found, defaulting to player_number"
                )
                order_column = PlayerTeamTournamentDB.player_number

            try:
                order_column_two = getattr(
                    PlayerTeamTournamentDB, order_by_two, PlayerTeamTournamentDB.id
                )
            except AttributeError:
                self.logger.warning(f"Order column {order_by_two} not found, defaulting to id")
                order_column_two = PlayerTeamTournamentDB.id

            order_expr = order_column.asc() if ascending else order_column.desc()
            order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            players = result.scalars().all()

            return PaginatedPlayerTeamTournamentResponse(
                data=[PlayerTeamTournamentSchema.model_validate(p) for p in players],
                metadata=PaginationMetadata(
                    page=(skip // limit) + 1,
                    items_per_page=limit,
                    total_items=total_items,
                    total_pages=total_pages,
                    has_next=(skip + limit) < total_items,
                    has_previous=skip > 0,
                ),
            )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching tournament players with pagination and details",
        return_value_on_not_found=None,
    )
    async def search_tournament_players_with_pagination_details(
        self,
        tournament_id: int,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "player_number",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedPlayerTeamTournamentWithDetailsResponse:
        self.logger.debug(
            f"Search tournament players with details: tournament_id={tournament_id}, query={search_query}, "
            f"skip={skip}, limit={limit}, order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            if search_query:
                search_pattern = f"%{search_query}%"
                base_query = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                    .join(PlayerDB, PlayerTeamTournamentDB.player_id == PlayerDB.id)
                    .join(PersonDB, PlayerDB.person_id == PersonDB.id)
                    .join(TeamDB, PlayerTeamTournamentDB.team_id == TeamDB.id)
                    .outerjoin(PositionDB, PlayerTeamTournamentDB.position_id == PositionDB.id)
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.position),
                    )
                    .where(
                        PlayerTeamTournamentDB.player_number.ilike(search_pattern)
                        | PersonDB.first_name.ilike(search_pattern).collate("en-US-x-icu")
                        | PersonDB.second_name.ilike(search_pattern).collate("en-US-x-icu")
                        | TeamDB.title.ilike(search_pattern).collate("en-US-x-icu")
                    )
                    .distinct()
                )
            else:
                base_query = (
                    select(PlayerTeamTournamentDB)
                    .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
                    .options(
                        selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                        selectinload(PlayerTeamTournamentDB.team),
                        selectinload(PlayerTeamTournamentDB.position),
                    )
                )

            count_stmt = select(func.count(func.distinct(PlayerTeamTournamentDB.id))).select_from(
                base_query
            )
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            total_pages = ceil(total_items / limit) if limit > 0 else 0

            try:
                order_column = getattr(
                    PlayerTeamTournamentDB, order_by, PlayerTeamTournamentDB.player_number
                )
            except AttributeError:
                self.logger.warning(
                    f"Order column {order_by} not found, defaulting to player_number"
                )
                order_column = PlayerTeamTournamentDB.player_number

            try:
                order_column_two = getattr(
                    PlayerTeamTournamentDB, order_by_two, PlayerTeamTournamentDB.id
                )
            except AttributeError:
                self.logger.warning(f"Order column {order_by_two} not found, defaulting to id")
                order_column_two = PlayerTeamTournamentDB.id

            order_expr = order_column.asc() if ascending else order_column.desc()
            order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            players = result.scalars().all()

            players_with_details = []
            for p in players:
                players_with_details.append(
                    {
                        "id": p.id,
                        "player_team_tournament_eesl_id": p.player_team_tournament_eesl_id,
                        "player_id": p.player_id,
                        "position_id": p.position_id,
                        "team_id": p.team_id,
                        "tournament_id": p.tournament_id,
                        "player_number": p.player_number,
                        "first_name": p.player.person.first_name
                        if p.player and p.player.person
                        else None,
                        "second_name": p.player.person.second_name
                        if p.player and p.player.person
                        else None,
                        "team_title": p.team.title if p.team else None,
                        "position_title": p.position.title if p.position else None,
                    }
                )

            return PaginatedPlayerTeamTournamentWithDetailsResponse(
                data=[
                    PlayerTeamTournamentWithDetailsSchema.model_validate(p)
                    for p in players_with_details
                ],
                metadata=PaginationMetadata(
                    page=(skip // limit) + 1,
                    items_per_page=limit,
                    total_items=total_items,
                    total_pages=total_pages,
                    has_next=(skip + limit) < total_items,
                    has_previous=skip > 0,
                ),
            )
