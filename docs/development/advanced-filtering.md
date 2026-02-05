# Advanced Filtering Patterns

## Filtering by Relationship Exclusion

Use SQLAlchemy `NOT EXISTS` for entities not related to another entity.

### Example: Persons Not in Sport

```python
from sqlalchemy import exists

@handle_service_exceptions(
    item_name=ITEM,
    operation="fetching persons not in sport",
    return_value_on_not_found=None,
)
async def get_persons_not_in_sport(
    self,
    sport_id: int,
    search_query: str | None = None,
    skip: int = 0,
    limit: int = 20,
    order_by: str = "second_name",
    order_by_two: str = "id",
    ascending: bool = True,
) -> PaginatedPersonResponse:
    async with self.db.get_session_maker()() as session:
        subquery = select(PlayerDB.id).where(
            PlayerDB.person_id == PersonDB.id,
            PlayerDB.sport_id == sport_id,
        )

        base_query = select(PersonDB).where(~exists(subquery))
        base_query = await self._apply_search_filters(
            base_query,
            [(PersonDB, "first_name"), (PersonDB, "second_name")],
            search_query,
        )

        count_stmt = select(func.count()).select_from(base_query.subquery())
        count_result = await session.execute(count_stmt)
        total_items = count_result.scalar() or 0

        order_expr, order_expr_two = await self._build_order_expressions(
            PersonDB, order_by, order_by_two, ascending, PersonDB.second_name, PersonDB.id
        )

        data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
        result = await session.execute(data_query)
        persons = result.scalars().all()

        return PaginatedPersonResponse(
            data=[PersonSchema.model_validate(p) for p in persons],
            metadata=PaginationMetadata(
                **await self._calculate_pagination_metadata(total_items, skip, limit),
            ),
        )
```

### Endpoint Implementation

```python
@router.get(
    "/not-in-sport/{sport_id}",
    response_model=PaginatedPersonResponse,
)
async def get_persons_not_in_sport_endpoint(
    sport_id: int,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    order_by: str = Query("second_name", description="First sort column"),
    order_by_two: str = Query("id", description="Second sort column"),
    ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
    search: str | None = Query(None, description="Search query for full-text search"),
):
    skip = (page - 1) * items_per_page
    response = await self.service.get_persons_not_in_sport(
        sport_id=sport_id,
        search_query=search,
        skip=skip,
        limit=items_per_page,
        order_by=order_by,
        order_by_two=order_by_two,
        ascending=ascending,
    )
    return response
```

## Best Practices

- Use `NOT EXISTS` instead of `NOT IN`
- Apply search filters after the exclusion filter
- Persons without players are automatically included
- Reuse `SearchPaginationMixin` for consistent pagination

## Pagination Metadata Consistency

All paginated endpoints must use `PaginationMetadata` from `src/core/schema_helpers.py`:

```python
class PaginationMetadata(BaseModel):
    page: int
    items_per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
```

Notes:

- Count endpoints return `{"total_items": count}`
- Use this schema consistently across domains
