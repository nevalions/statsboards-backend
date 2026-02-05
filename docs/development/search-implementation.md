# Search Implementation

When adding search functionality to a domain:

## 1. Schema Updates

```python
class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class Paginated{Entity}Response(BaseModel):
    data: list[{Entity}Schema]
    metadata: PaginationMetadata
```

## 2. Service Layer Implementation

```python
from math import ceil
from sqlalchemy import select, func

@handle_service_exceptions(
    item_name=ITEM,
    operation="searching {entity}s with pagination",
    return_value_on_not_found=None,
)
async def search_{entity}s_with_pagination(
    self,
    search_query: str | None = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "{default_field}",
    order_by_two: str = "id",
    ascending: bool = True,
) -> Paginated{Entity}Response:
    async with self.db.get_session_maker()() as session:
        base_query = select({Model}DB)

        if search_query:
            search_pattern = f"%{search_query}%"
            base_query = base_query.where(
                ({Model}DB.field1.ilike(search_pattern).collate("en-US-x-icu"))
                | ({Model}DB.field2.ilike(search_pattern).collate("en-US-x-icu"))
            )

        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_stmt)
        total_items = count_result.scalar() or 0
        total_pages = ceil(total_items / limit) if limit > 0 else 0

        order_column = getattr({Model}DB, order_by, {Model}DB.{default_field})
        order_column_two = getattr({Model}DB, order_by_two, {Model}DB.id)
        order_expr = order_column.asc() if ascending else order_column.desc()
        order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

        data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
        result = await session.execute(data_query)
        {entity}s = result.scalars().all()

        return Paginated{Entity}Response(
            data=[{Entity}Schema.model_validate(e) for e in {entity}s],
            metadata=PaginationMetadata(
                page=(skip // limit) + 1,
                items_per_page=limit,
                total_items=total_items,
                total_pages=total_pages,
                has_next=(skip + limit) < total_items,
                has_previous=skip > 0,
            ),
        )
```

## 3. Router Layer Updates

```python
@router.get(
    "/paginated",
    response_model=Paginated{Entity}Response,
)
async def get_all_{entity}s_paginated_endpoint(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    order_by: str = Query("{default_field}", description="First sort column"),
    order_by_two: str = Query("id", description="Second sort column"),
    ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
    search: str | None = Query(None, description="Search query for text search"),
):
    skip = (page - 1) * items_per_page
    response = await self.service.search_{entity}s_with_pagination(
        search_query=search,
        skip=skip,
        limit=items_per_page,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
    )
    return response
```

## Key Implementation Details

1. Search uses `ilike()` with ICU collation for international text
2. Pagination metadata is required for all paginated endpoints
3. Dual column ordering ensures stable pagination
4. `search=None` returns all records with pagination
5. Use decorator with `return_value_on_not_found=None` for empty responses

## Ordering by Joined Table Fields

When ordering by fields from joined tables, use mapping-based order expressions.

```python
async def _build_order_expressions_with_joins(
    self,
    order_by: str,
    order_by_two: str | None,
    ascending: bool,
) -> tuple:
    field_mapping = {
        "id": PlayerTeamTournamentDB.id,
        "player_number": PlayerTeamTournamentDB.player_number,
        "player_team_tournament_eesl_id": PlayerTeamTournamentDB.player_team_tournament_eesl_id,
        "first_name": PersonDB.first_name,
        "second_name": PersonDB.second_name,
        "team_title": TeamDB.title,
        "position_title": PositionDB.title,
    }

    return await self._build_order_expressions_with_mapping(
        field_mapping=field_mapping,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
        default_column=PlayerTeamTournamentDB.player_number,
        default_column_two=PlayerTeamTournamentDB.id,
    )
```

## Common Pitfalls in Paginated Search

### Incorrect Count Query Pattern

Wrong (inflates counts with joins):

```python
count_stmt = select(func.count(func.distinct(ModelDB.id))).select_from(base_query)
```

Correct:

```python
count_stmt = select(func.count()).select_from(base_query.subquery())
```

## Search Testing Guidelines

- Add tests for count accuracy when joins are present
- Verify `total_items` matches distinct model rows
- Include cases with combined filters (e.g., `search` + secondary filter)

Example test idea:

```python
async def test_pagination_with_joins_correct_count():
    # Create data with joins
    # Assert total_items matches distinct model rows
    ...
```

## Example: Person Domain

See `src/person/`:

- Schema: `PaginationMetadata`, `PaginatedPersonResponse`
- Service: `PersonServiceDB.search_persons_with_pagination()`
- Router: `PersonAPIRouter.get_all_persons_paginated_endpoint()`

## Test Database Setup

No special setup required for ilike-based search. Run with:

```bash
pytest tests/test_{domain}_search.py
```

## PostgreSQL pg_trgm Optimization (Optional)

See `docs/PG_TRGM_SEARCH_OPTIMIZATION.md` for full details. Use when datasets are large and `%query%` searches are slow.
