from sqlalchemy import func, select

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, SponsorDB
from src.core.models.base import Database
from src.core.models.mixins.search_pagination_mixin import SearchPaginationMixin
from src.core.schema_helpers import PaginationMetadata
from src.logging_config import get_logger
from src.sponsors.schemas import (
    PaginatedSponsorResponse,
    SponsorSchema,
    SponsorSchemaCreate,
    SponsorSchemaUpdate,
)

ITEM = "SPONSOR"


class SponsorServiceDB(BaseServiceDB, SearchPaginationMixin):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, SponsorDB)
        self.logger = get_logger("backend_logger_SponsorServiceDB", self)
        self.logger.debug("Initialized SponsorServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: SponsorSchemaCreate,
    ) -> SponsorDB:
        self.logger.debug(f"Creating {ITEM} {item}")
        return await super().create(item)

    async def update(
        self,
        item_id: int,
        item: SponsorSchemaUpdate,
        **kwargs,
    ) -> SponsorDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching sponsors with pagination",
        return_value_on_not_found=None,
    )
    async def search_sponsors_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "title",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedSponsorResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.get_session_maker()() as session:
            base_query = select(SponsorDB)

            base_query = await self._apply_search_filters(
                base_query,
                [(SponsorDB, "title")],
                search_query,
            )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                SponsorDB, order_by, order_by_two, ascending, SponsorDB.title, SponsorDB.id
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            sponsors = result.scalars().all()

            return PaginatedSponsorResponse(
                data=[SponsorSchema.model_validate(s) for s in sponsors],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
