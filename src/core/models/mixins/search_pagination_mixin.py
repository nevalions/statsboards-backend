import logging
from math import ceil
from typing import TYPE_CHECKING

from sqlalchemy import Integer as SAInteger
from sqlalchemy import String, cast, or_

if TYPE_CHECKING:
    from src.core.models.base import Base, Database


class SearchPaginationMixin:
    """Mixin for search with pagination using ICU collation and dual-column ordering"""

    if TYPE_CHECKING:
        logger: logging.LoggerAdapter
        model: type["Base"]
        db: "Database"

    async def _build_search_pattern(self, search_query: str) -> str:
        """Build search pattern with wildcards"""
        return f"%{search_query}%"

    async def _apply_search_filters(
        self,
        base_query,
        search_fields: list,
        search_query: str | None,
    ):
        """Apply ILIKE search to multiple fields with ICU collation. Supports both string and integer fields (integers are cast to strings for search)."""
        if not search_query:
            return base_query

        search_pattern = await self._build_search_pattern(search_query)
        conditions = []
        for model, model_field in search_fields:
            column = getattr(model, model_field)

            if isinstance(column.type, SAInteger):
                column = cast(column, String)
            conditions.append(column.ilike(search_pattern).collate("en-US-x-icu"))
        return base_query.where(or_(*conditions))

    async def _get_column_with_fallback(
        self,
        model,
        column_name: str,
        default_column,
    ):
        """Get column with AttributeError logging and fallback"""
        try:
            return getattr(model, column_name)
        except AttributeError:
            self.logger.warning(
                f"Order column {column_name} not found for {model.__name__}, "
                f"defaulting to {default_column.name}"
            )
            return default_column

    async def _build_order_expressions(
        self,
        model,
        order_by: str,
        order_by_two: str,
        ascending: bool,
        default_column,
        default_column_two,
    ):
        """Build two-level order expressions with fallback"""
        order_column = await self._get_column_with_fallback(model, order_by, default_column)
        order_column_two = await self._get_column_with_fallback(
            model, order_by_two, default_column_two
        )

        order_expr = order_column.asc() if ascending else order_column.desc()
        order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

        return order_expr, order_expr_two

    async def _build_order_expressions_with_mapping(
        self,
        field_mapping: dict[str, object],
        order_by: str,
        order_by_two: str | None,
        ascending: bool,
        default_column,
        default_column_two,
    ):
        """Build order expressions using field mapping for joined table columns.

        Args:
            field_mapping: Dictionary mapping field names to SQLAlchemy column expressions
            order_by: Primary order by field name
            order_by_two: Secondary order by field name (optional)
            ascending: Sort direction (True for ascending)
            default_column: Default column for order_by if not in mapping
            default_column_two: Default column for order_by_two if not in mapping

        Returns:
            Tuple of (order_expr, order_expr_two or None)
        """
        order_column = field_mapping.get(order_by, default_column)
        order_expr = order_column.asc() if ascending else order_column.desc()

        order_expr_two = None
        if order_by_two:
            order_column_two = field_mapping.get(order_by_two, default_column_two)
            order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

        return order_expr, order_expr_two

    async def _calculate_pagination_metadata(
        self,
        total_items: int,
        skip: int,
        limit: int,
    ) -> dict:
        """Calculate pagination metadata from query results"""
        total_pages = ceil(total_items / limit) if limit > 0 else 0
        return {
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "items_per_page": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": (skip + limit) < total_items,
            "has_previous": skip > 0,
        }
