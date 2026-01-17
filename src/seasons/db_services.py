from fastapi import HTTPException
from sqlalchemy import and_, asc, select
from sqlalchemy.sql import func

from src.core.decorators import handle_service_exceptions
from src.core.models import (
    BaseServiceDB,
    MatchDB,
    SeasonDB,
    SportDB,
    TeamDB,
    TournamentDB,
)
from src.core.models.base import Database
from src.core.models.mixins.search_pagination_mixin import SearchPaginationMixin
from src.core.schema_helpers import PaginationMetadata
from src.logging_config import get_logger

from .schemas import (
    PaginatedSeasonResponse,
    SeasonSchema,
    SeasonSchemaCreate,
    SeasonSchemaUpdate,
)

ITEM = "SEASON"


class SeasonServiceDB(BaseServiceDB, SearchPaginationMixin):
    def __init__(self, database: Database) -> None:
        super().__init__(
            database,
            model=SeasonDB,
        )
        self.logger = get_logger("backend_logger_SeasonServiceDB", self)
        self.logger.debug("Initialized SeasonServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: SeasonSchemaCreate) -> SeasonDB:
        self.logger.debug(f"Creat {ITEM}:{item}")
        return await super().create(item)

    @handle_service_exceptions(item_name=ITEM, operation="updating", return_value_on_not_found=None)
    async def update(
        self,
        item_id: int,
        item: SeasonSchemaUpdate,
        **kwargs,
    ) -> SeasonDB | None:
        self.logger.debug(f"Update {ITEM} with id:{item_id}")
        if item.year is None:
            raise HTTPException(
                status_code=409,
                detail=f"Error updating {self.model.__name__}. Check input data. {ITEM}",
            )
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    async def get_season_by_year(self, season_year: int) -> SeasonDB | None:
        async with self.db.async_session() as session:
            self.logger.debug(f"Get {ITEM}s by year id:{season_year}")
            season = await session.execute(select(SeasonDB).filter_by(year=season_year))
            return season.scalars().one_or_none()

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching tournaments", return_value_on_not_found=[]
    )
    async def get_tournaments_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[TournamentDB]:
        self.logger.debug(f"Get tournaments by {ITEM} year:{year}")
        async with self.db.async_session() as session:
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .where(getattr(SeasonDB, key) == year)
                .order_by(asc(TournamentDB.title))
            )
            results = await session.execute(stmt)
            tournaments = results.scalars().all()
            return tournaments

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching tournaments", return_value_on_not_found=[]
    )
    async def get_tournaments_by_year_and_sport(
        self,
        year: int,
        sport_id: int,
    ) -> list[TournamentDB]:
        async with self.db.async_session() as session:
            self.logger.debug(f"Get tournaments by {ITEM} year:{year} id:{sport_id}")
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.year == year, SportDB.id == sport_id))
                .order_by(asc(TournamentDB.title))
            )
            results = await session.execute(stmt)
            tournaments = results.scalars().all()
            self.logger.info(f"Got tournaments: {tournaments}")
            return tournaments

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching tournaments", return_value_on_not_found=[]
    )
    async def get_tournaments_by_season_and_sport_ids(
        self,
        season_id: int,
        sport_id: int,
    ) -> list[TournamentDB]:
        self.logger.debug(f"Get tournaments by {ITEM} id:{season_id} and sport_id:{sport_id}")
        async with self.db.async_session() as session:
            stmt = (
                select(TournamentDB)
                .join(SeasonDB, TournamentDB.season_id == SeasonDB.id)
                .join(SportDB, TournamentDB.sport_id == SportDB.id)
                .where(and_(SeasonDB.id == season_id, SportDB.id == sport_id))
                .order_by(asc(TournamentDB.title))
            )
            results = await session.execute(stmt)
            tournaments = results.scalars().all()
            self.logger.debug(f"Got number of tournaments: {len(tournaments)}")
            return tournaments

    async def get_teams_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[TeamDB]:
        self.logger.debug(f"Get teams by {ITEM} year:{year}")
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="teams",
        )

    async def get_matches_by_year(
        self,
        year: int,
        key: str = "year",
    ) -> list[MatchDB]:
        self.logger.debug(f"Get teams by {ITEM} year:{year}")
        return await self.get_related_items_by_two(
            filter_key=key,
            filter_value=year,
            second_model=TournamentDB,
            related_property="tournaments",
            second_level_property="matches",
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching seasons with pagination",
        return_value_on_not_found=None,
    )
    async def search_seasons_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "year",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedSeasonResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = select(SeasonDB)

            base_query = await self._apply_search_filters(
                base_query,
                [(SeasonDB, "description")],
                search_query,
            )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                SeasonDB, order_by, order_by_two, ascending, SeasonDB.year, SeasonDB.id
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            seasons = result.scalars().all()

            return PaginatedSeasonResponse(
                data=[SeasonSchema.model_validate(s) for s in seasons],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
