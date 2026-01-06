from math import ceil

from sqlalchemy import select
from sqlalchemy.sql import func

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, PersonDB
from src.core.models.base import Database

from ..logging_config import get_logger
from .schemas import (
    PaginatedPersonResponse,
    PaginationMetadata,
    PersonSchema,
    PersonSchemaCreate,
    PersonSchemaUpdate,
)

ITEM = "PERSON"


class PersonServiceDB(BaseServiceDB):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, PersonDB)
        self.logger = get_logger("backend_logger_PersonServiceDB", self)
        self.logger.debug("Initialized PersonServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: PersonSchemaCreate | PersonSchemaUpdate,
    ) -> PersonDB:
        self.logger.debug(f"Starting to create PersonDB with data: {item.__dict__}")
        return await super().create(item)

    async def create_or_update_person(
        self,
        p: PersonSchemaCreate | PersonSchemaUpdate,
    ) -> PersonDB | None:
        return await super().create_or_update(p, eesl_field_name="person_eesl_id")

    async def get_person_by_eesl_id(
        self,
        value: int | str,
        field_name: str = "person_eesl_id",
    ) -> PersonDB | None:
        self.logger.debug(f"Get {ITEM} {field_name}:{value}")
        return await self.get_item_by_field_value(
            value=value,
            field_name=field_name,
        )

    async def update(
        self,
        item_id: int,
        item: PersonSchemaUpdate,
        **kwargs,
    ) -> PersonDB:
        self.logger.debug(f"Update {ITEM}:{item_id}")
        return await super().update(
            item_id,
            item,
            **kwargs,
        )

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching persons with pagination", return_value_on_not_found=[]
    )
    async def get_all_persons_with_pagination(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "second_name",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> list[PersonDB]:
        self.logger.debug(
            f"Get {ITEM} with pagination: skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )
        return await self.get_all_with_pagination(
            skip=skip,
            limit=limit,
            order_by=order_by,
            order_by_two=order_by_two,
            ascending=ascending,
        )

    @handle_service_exceptions(
        item_name=ITEM, operation="fetching persons count", return_value_on_not_found=0
    )
    async def get_persons_count(self) -> int:
        self.logger.debug(f"Get {ITEM} count")
        return await self.get_count()

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching persons with pagination",
        return_value_on_not_found=None,
    )
    async def search_persons_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "second_name",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedPersonResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.async_session() as session:
            base_query = select(PersonDB)

            if search_query:
                search_pattern = f"%{search_query}%"
                base_query = base_query.where(
                    (PersonDB.first_name.ilike(search_pattern))
                    | (PersonDB.second_name.ilike(search_pattern))
                )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            total_pages = ceil(total_items / limit) if limit > 0 else 0

            try:
                order_column = getattr(PersonDB, order_by, PersonDB.second_name)
            except AttributeError:
                self.logger.warning(f"Order column {order_by} not found, defaulting to second_name")
                order_column = PersonDB.second_name

            try:
                order_column_two = getattr(PersonDB, order_by_two, PersonDB.id)
            except AttributeError:
                self.logger.warning(f"Order column {order_by_two} not found, defaulting to id")
                order_column_two = PersonDB.id

            order_expr = order_column.asc() if ascending else order_column.desc()
            order_expr_two = order_column_two.asc() if ascending else order_column_two.desc()

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            persons = result.scalars().all()

            return PaginatedPersonResponse(
                data=[PersonSchema.model_validate(p) for p in persons],
                metadata=PaginationMetadata(
                    page=(skip // limit) + 1,
                    items_per_page=limit,
                    total_items=total_items,
                    total_pages=total_pages,
                    has_next=(skip + limit) < total_items,
                    has_previous=skip > 0,
                ),
            )
