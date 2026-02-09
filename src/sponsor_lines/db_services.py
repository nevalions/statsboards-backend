from __future__ import annotations

from sqlalchemy import func, select

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, SponsorLineDB
from src.core.models.base import Database
from src.core.models.mixins.search_pagination_mixin import SearchPaginationMixin
from src.core.schema_helpers import PaginationMetadata

from ..logging_config import get_logger
from .schemas import (
    PaginatedSponsorLineResponse,
    SponsorLineSchema,
    SponsorLineSchemaCreate,
    SponsorLineSchemaUpdate,
)

ITEM = "SPONSOR_LINE"


class SponsorLineServiceDB(BaseServiceDB, SearchPaginationMixin):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, SponsorLineDB)
        self.logger = get_logger("SponsorLineServiceDB", self)
        self.logger.debug("Initialized SponsorLineServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: SponsorLineSchemaCreate,
    ) -> SponsorLineDB:
        self.logger.debug(f"Creating {ITEM}")
        return await super().create(item)

    async def update(
        self,
        item_id: int,
        item: SponsorLineSchemaUpdate,
        **kwargs,
    ) -> SponsorLineDB | None:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching sponsor lines with pagination",
        return_value_on_not_found=None,
    )
    async def search_sponsor_lines_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "title",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedSponsorLineResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.get_session_maker()() as session:
            base_query = select(SponsorLineDB)

            base_query = await self._apply_search_filters(
                base_query,
                [(SponsorLineDB, "title")],
                search_query,
            )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                SponsorLineDB,
                order_by,
                order_by_two,
                ascending,
                SponsorLineDB.title,
                SponsorLineDB.id,
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            sponsor_lines = result.scalars().all()

            return PaginatedSponsorLineResponse(
                data=[SponsorLineSchema.model_validate(s) for s in sponsor_lines],
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
