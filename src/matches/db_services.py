from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from src.core.models import (
    BaseServiceDB,
    GameClockDB,
    MatchDataDB,
    MatchDB,
    PlayClockDB,
    PlayerMatchDB,
    PlayerTeamTournamentDB,
    ScoreboardDB,
    SponsorLineDB,
    SportDB,
    TeamDB,
    handle_service_exceptions,
)
from src.core.models.base import Database
from src.core.schema_helpers import PaginationMetadata
from src.core.service_registry import get_service_registry
from src.logging_config import get_logger

from .schemas import (
    MatchSchema,
    MatchSchemaCreate,
    MatchSchemaUpdate,
    PaginatedMatchResponse,
)

ITEM = "MATCH"


class MatchServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, MatchDB)
        self.logger = get_logger("backend_logger_MatchServiceDB", self)
        self.logger.debug("Initialized MatchServiceDB")
        self._service_registry = None

    @property
    def service_registry(self):
        if self._service_registry is None:
            self._service_registry = get_service_registry()
        return self._service_registry

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: MatchSchemaCreate | MatchSchemaUpdate,
    ) -> MatchDB:
        self.logger.debug(f"Starting to create MatchDB with data: {item.__dict__}")
        return await super().create(item)

    async def create_or_update_match(self, m: MatchSchemaCreate) -> MatchDB:
        return await super().create_or_update(m, eesl_field_name="match_eesl_id")

    async def get_match_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "match_eesl_id",
    ) -> MatchDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: MatchSchemaUpdate,
        **kwargs,
    ) -> MatchDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching match with details",
        return_value_on_not_found=None,
    )
    async def get_match_with_details(
        self,
        match_id: int,
    ) -> MatchDB | None:
        self.logger.debug(f"Get {ITEM} with details id:{match_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(MatchDB)
                .where(MatchDB.id == match_id)
                .options(
                    joinedload(MatchDB.team_a),
                    joinedload(MatchDB.team_b),
                    joinedload(MatchDB.tournaments),
                    joinedload(MatchDB.main_sponsor),
                    joinedload(MatchDB.sponsor_line),
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching sport by match_id",
        return_value_on_not_found=None,
    )
    async def get_sport_by_match_id(self, match_id: int) -> SportDB | None:
        self.logger.debug(f"Get sport by {ITEM} id:{match_id}")
        tournament_service = self.service_registry.get("tournament")
        sport_service = self.service_registry.get("sport")
        match = await self.get_by_id(match_id)
        if match:
            tournament = await tournament_service.get_by_id(match.tournament_id)
            if tournament:
                return await sport_service.get_by_id(tournament.sport_id)
        return None

    @handle_service_exceptions(
        item_name=ITEM,
        operation="fetching teams by match_id",
        return_value_on_not_found=None,
    )
    async def get_teams_by_match_id(
        self,
        match_id: int,
    ) -> dict | None:
        self.logger.debug(f"Get teams by {ITEM} id:{match_id}")
        async with self.db.async_session():
            team_service = self.service_registry.get("team")
            match = await self.get_by_id(match_id)
            if match:
                home_team = await team_service.get_by_id(match.team_a_id)
                away_team = await team_service.get_by_id(match.team_b_id)
                return {
                    "home_team": home_team,
                    "away_team": away_team,
                }
            return None

    async def get_match_sponsor_line(self, match_id: int) -> SponsorLineDB | None:
        self.logger.debug(f"Get sponsor_line by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(match_id, "sponsor_line")
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_matchdata_by_match(
        self,
        match_id: int,
    ) -> MatchDataDB | None:
        self.logger.debug(f"Get match_data by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_data",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_playclock_by_match(
        self,
        match_id: int,
    ) -> PlayClockDB | None:
        self.logger.debug(f"Get match_playclock by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_playclock",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def get_gameclock_by_match(
        self,
        match_id: int,
    ) -> GameClockDB | None:
        self.logger.debug(f"Get match_gameclock by {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_gameclock",
        )
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting teams v2",
        return_value_on_not_found=None,
    )
    async def get_teams_by_match(
        self,
        match_id: int,
    ) -> dict | None:
        self.logger.debug(f"Get teams v2 by {ITEM} id:{match_id}")
        match = await self.get_related_items(
            match_id,
        )
        if match:
            team_a = await self.get_by_id_and_model(
                model=TeamDB,
                item_id=match.team_a_id,
            )
            team_b = await self.get_by_id_and_model(
                model=TeamDB,
                item_id=match.team_b_id,
            )

            return {
                "team_a": team_a.__dict__,
                "team_b": team_b.__dict__,
            }
        return None

    @handle_service_exceptions(
        item_name=ITEM, operation="getting players", return_value_on_not_found=[]
    )
    async def get_players_by_match(
        self,
        match_id: int,
    ) -> list[PlayerMatchDB]:
        self.logger.debug(f"Get players by {ITEM} id:{match_id}")
        async with self.db.async_session() as session:
            stmt = select(PlayerMatchDB).where(PlayerMatchDB.match_id == match_id)

            results = await session.execute(stmt)
            players = results.scalars().all()
            return players

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting players with full data",
        return_value_on_not_found=[],
    )
    async def get_player_by_match_full_data(self, match_id: int) -> list[dict]:
        self.logger.debug(f"Get players with full data by {ITEM} id:{match_id}")
        from src.core.models.player import PlayerDB
        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with self.db.async_session() as session:
            stmt = (
                select(PlayerMatchDB)
                .where(PlayerMatchDB.match_id == match_id)
                .options(
                    selectinload(PlayerMatchDB.player_team_tournament)
                    .selectinload(PlayerTeamTournamentDB.player)
                    .selectinload(PlayerDB.person),
                    selectinload(PlayerMatchDB.match_position),
                    selectinload(PlayerMatchDB.team),
                )
            )

            results = await session.execute(stmt)
            players = results.scalars().all()

            players_with_data = []
            for player in players:
                players_with_data.append(
                    {
                        "id": player.id,
                        "player_id": (
                            player.player_team_tournament.player_id
                            if player.player_team_tournament
                            else None
                        ),
                        "player": (
                            player.player_team_tournament.player
                            if player.player_team_tournament
                            else None
                        ),
                        "team": player.team,
                        "position": (
                            {
                                **player.match_position.__dict__,
                                "category": player.match_position.category,
                            }
                            if player.match_position
                            else None
                        ),
                        "player_team_tournament": player.player_team_tournament,
                        "person": (
                            player.player_team_tournament.player.person
                            if player.player_team_tournament
                            and player.player_team_tournament.player
                            else None
                        ),
                        "is_starting": player.is_starting,
                        "starting_type": player.starting_type,
                    }
                )

            return players_with_data

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting players with full data optimized",
        return_value_on_not_found=[],
    )
    async def get_players_with_full_data_optimized(
        self,
        match_id: int,
    ) -> list[dict]:
        self.logger.debug(f"Get players with full data optimized by {ITEM} id:{match_id}")
        from src.core.models.player import PlayerDB
        from src.core.models.player_team_tournament import PlayerTeamTournamentDB

        async with self.db.async_session() as session:
            stmt = (
                select(PlayerMatchDB)
                .where(PlayerMatchDB.match_id == match_id)
                .options(
                    selectinload(PlayerMatchDB.player_team_tournament)
                    .selectinload(PlayerTeamTournamentDB.player)
                    .selectinload(PlayerDB.person),
                    selectinload(PlayerMatchDB.match_position),
                    selectinload(PlayerMatchDB.team),
                )
            )

            results = await session.execute(stmt)
            players = results.scalars().all()

            players_with_data = []
            for player in players:
                players_with_data.append(
                    {
                        "id": player.id,
                        "player_id": (
                            player.player_team_tournament.player_id
                            if player.player_team_tournament
                            else None
                        ),
                        "player": (
                            player.player_team_tournament.player
                            if player.player_team_tournament
                            else None
                        ),
                        "team": player.team,
                        "position": (
                            {
                                **player.match_position.__dict__,
                                "category": player.match_position.category,
                            }
                            if player.match_position
                            else None
                        ),
                        "player_team_tournament": player.player_team_tournament,
                        "person": (
                            player.player_team_tournament.player.person
                            if player.player_team_tournament
                            and player.player_team_tournament.player
                            else None
                        ),
                        "is_starting": player.is_starting,
                        "starting_type": player.starting_type,
                    }
                )

            return players_with_data

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting scoreboard",
        return_value_on_not_found=None,
    )
    async def get_scoreboard_by_match(
        self,
        match_id: int,
    ) -> ScoreboardDB | None:
        self.logger.debug(f"Getting scoreboard for {ITEM} id:{match_id}")
        result = await self.get_related_item_level_one_by_id(
            match_id,
            "match_scoreboard",
        )
        self.logger.debug(f"Got scoreboard successfully. Result: {result}")
        if result:
            if hasattr(result, "__len__"):
                if len(result) > 0:
                    return result[0]  # type: ignore[return-value]
                return None
            return result  # type: ignore[return-value]
        return None

    async def _get_available_players(
        self, session, team_id: int, tournament_id: int, match_id: int
    ) -> list[dict]:
        """Get players available for match (not already in match)."""
        from src.core.models.player import PlayerDB

        subquery = (
            select(PlayerMatchDB.player_team_tournament_id)
            .where(PlayerMatchDB.match_id == match_id)
            .where(PlayerMatchDB.team_id == team_id)
        )

        stmt = (
            select(PlayerTeamTournamentDB)
            .where(PlayerTeamTournamentDB.team_id == team_id)
            .where(PlayerTeamTournamentDB.tournament_id == tournament_id)
            .where(~PlayerTeamTournamentDB.id.in_(subquery))
            .options(
                selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                selectinload(PlayerTeamTournamentDB.position),
                selectinload(PlayerTeamTournamentDB.team),
            )
        )

        results = await session.execute(stmt)
        available_players = results.scalars().all()

        return [
            {
                "id": pt.id,
                "player_id": pt.player_id,
                "player_team_tournament": pt,
                "person": pt.player.person if pt.player else None,
                "position": pt.position,
                "team": pt.team,
            }
            for pt in available_players
        ]

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting match full context",
        return_value_on_not_found=None,
    )
    async def get_match_full_context(self, match_id: int) -> dict | None:
        """Get match with all initialization data: teams, sport, positions, players."""
        self.logger.debug(f"Get match full context for {ITEM} id:{match_id}")

        from src.core.models.player import PlayerDB

        async with self.db.async_session() as session:
            stmt = (
                select(MatchDB)
                .where(MatchDB.id == match_id)
                .options(
                    selectinload(MatchDB.team_a),
                    selectinload(MatchDB.team_b),
                    selectinload(MatchDB.tournaments),
                )
            )

            result = await session.execute(stmt)
            match = result.scalar_one_or_none()

            if not match:
                return None

            tournament = match.tournaments if match.tournaments else None

            if tournament:
                stmt_sport = (
                    select(SportDB)
                    .where(SportDB.id == tournament.sport_id)
                    .options(selectinload(SportDB.positions))
                )
                result_sport = await session.execute(stmt_sport)
                sport = result_sport.scalar_one_or_none()
            else:
                sport = None

            stmt_players = (
                select(PlayerMatchDB)
                .where(PlayerMatchDB.match_id == match_id)
                .options(
                    selectinload(PlayerMatchDB.player_team_tournament)
                    .selectinload(PlayerTeamTournamentDB.player)
                    .selectinload(PlayerDB.person),
                    selectinload(PlayerMatchDB.match_position),
                    selectinload(PlayerMatchDB.team),
                )
            )
            result_players = await session.execute(stmt_players)
            player_matches = result_players.scalars().all()

            home_available = await self._get_available_players(
                session, match.team_a_id, match.tournament_id, match_id
            )
            away_available = await self._get_available_players(
                session, match.team_b_id, match.tournament_id, match_id
            )

            home_roster = [
                {
                    "id": pm.id,
                    "player_id": pm.player_team_tournament.player_id
                    if pm.player_team_tournament
                    else None,
                    "match_player": pm,
                    "player_team_tournament": pm.player_team_tournament,
                    "player": pm.player_team_tournament.player
                    if pm.player_team_tournament
                    else None,
                    "person": (
                        pm.player_team_tournament.player.person
                        if pm.player_team_tournament and pm.player_team_tournament.player
                        else None
                    ),
                    "position": (
                        {
                            **pm.match_position.__dict__,
                            "category": pm.match_position.category,
                        }
                        if pm.match_position
                        else None
                    ),
                    "team": pm.team,
                    "is_starting": pm.is_starting,
                    "starting_type": pm.starting_type,
                }
                for pm in player_matches
                if pm.team_id == match.team_a_id
            ]

            away_roster = [
                {
                    "id": pm.id,
                    "player_id": pm.player_team_tournament.player_id
                    if pm.player_team_tournament
                    else None,
                    "match_player": pm,
                    "player_team_tournament": pm.player_team_tournament,
                    "player": pm.player_team_tournament.player
                    if pm.player_team_tournament
                    else None,
                    "person": (
                        pm.player_team_tournament.player.person
                        if pm.player_team_tournament and pm.player_team_tournament.player
                        else None
                    ),
                    "position": (
                        {
                            **pm.match_position.__dict__,
                            "category": pm.match_position.category,
                        }
                        if pm.match_position
                        else None
                    ),
                    "team": pm.team,
                    "is_starting": pm.is_starting,
                    "starting_type": pm.starting_type,
                }
                for pm in player_matches
                if pm.team_id == match.team_b_id
            ]

            return {
                "match": match.__dict__,
                "teams": {
                    "home": match.team_a.__dict__ if match.team_a else None,
                    "away": match.team_b.__dict__ if match.team_b else None,
                },
                "sport": {
                    **(sport.__dict__ if sport else {}),
                    "positions": [pos.__dict__ for pos in sport.positions] if sport else [],
                },
                "tournament": tournament.__dict__ if tournament else None,
                "players": {
                    "home_roster": home_roster,
                    "away_roster": away_roster,
                    "available_home": home_available,
                    "available_away": away_available,
                },
            }

    @handle_service_exceptions(
        item_name=ITEM,
        operation="getting available players for team in match",
        return_value_on_not_found=[],
    )
    async def get_available_players_for_team_in_match(
        self, match_id: int, team_id: int
    ) -> list[dict]:
        """Get available players for a specific team in a match (not already in match roster)."""
        from src.core.models.player import PlayerDB

        self.logger.debug(f"Get available players for team id:{team_id} in match id:{match_id}")

        async with self.db.async_session() as session:
            match = await session.get(MatchDB, match_id)
            if not match:
                return []

            subquery = (
                select(PlayerMatchDB.player_team_tournament_id)
                .where(PlayerMatchDB.match_id == match_id)
                .where(PlayerMatchDB.team_id == team_id)
            )

            stmt = (
                select(PlayerTeamTournamentDB)
                .where(PlayerTeamTournamentDB.team_id == team_id)
                .where(PlayerTeamTournamentDB.tournament_id == match.tournament_id)
                .where(~PlayerTeamTournamentDB.id.in_(subquery))
                .options(
                    selectinload(PlayerTeamTournamentDB.player).selectinload(PlayerDB.person),
                    selectinload(PlayerTeamTournamentDB.team),
                    selectinload(PlayerTeamTournamentDB.position),
                )
            )

            results = await session.execute(stmt)
            available_players = results.scalars().all()

            return [
                {
                    "id": pt.id,
                    "player_id": pt.player_id,
                    "player_team_tournament": pt,
                    "player": pt.player,
                    "person": pt.player.person if pt.player else None,
                    "position": pt.position,
                    "team": pt.team,
                    "player_number": pt.player_number,
                }
                for pt in available_players
            ]

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching matches with pagination",
        return_value_on_not_found=None,
    )
    async def search_matches_with_pagination(
        self,
        search_query: str | None = None,
        week: int | None = None,
        tournament_id: int | None = None,
        user_id: int | None = None,
        isprivate: bool | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "match_date",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedMatchResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, week={week}, tournament_id={tournament_id}, "
            f"skip={skip}, limit={limit}, order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = select(MatchDB)

            if user_id is not None:
                base_query = base_query.where(MatchDB.user_id == user_id)

            if isprivate is not None:
                base_query = base_query.where(MatchDB.isprivate == isprivate)

            if search_query:
                base_query = await self._apply_search_filters(
                    base_query,
                    [(MatchDB, "match_eesl_id")],
                    search_query,
                )

            if week is not None:
                base_query = base_query.where(MatchDB.week == week)

            if tournament_id is not None:
                base_query = base_query.where(MatchDB.tournament_id == tournament_id)

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                MatchDB, order_by, order_by_two, ascending, MatchDB.match_date, MatchDB.id
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            matches = result.scalars().all()

            return PaginatedMatchResponse(
                data=[MatchSchema.model_validate(m) for m in matches],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )

    # async def get_scoreboard_by_match(
    #     self,
    #     match_id: int,
    # ):
    #     return await self.get_related_item_level_one_by_id(
    #         match_id,
    #         "match_scoreboard",
    #     )


# async def get_match_db() -> MatchServiceDB:
#     yield MatchServiceDB(db)
#
#
# async def async_main() -> None:
#     match_service = MatchServiceDB(db)
#     # t = await team_service.get_team_by_id(1)
#     # t = await team_service.find_team_tournament_relation(6, 2)
#     # print(t)
#     # t = await team_service.get_team_by_eesl_id(1)
#     # u = await match_service.create_match()
#     # if t:
#     #     print(t.__dict__)
#
#
# if __name__ == "__main__":
#     asyncio.run(async_main())
