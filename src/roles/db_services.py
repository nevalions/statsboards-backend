from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.core.decorators import handle_service_exceptions
from src.core.models import BaseServiceDB, RoleDB, UserRoleDB
from src.core.models.base import Database
from src.core.models.mixins.search_pagination_mixin import SearchPaginationMixin
from src.core.schema_helpers import PaginationMetadata
from src.logging_config import get_logger

from .schemas import PaginatedRoleResponse, RoleSchema, RoleSchemaCreate, RoleSchemaUpdate

ITEM = "ROLE"


class RoleServiceDB(BaseServiceDB, SearchPaginationMixin):
    def __init__(
        self,
        database: Database,
    ) -> None:
        super().__init__(database, RoleDB)
        self.logger = get_logger("RoleServiceDB", self)
        self.logger.debug("Initialized RoleServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(
        self,
        item: RoleSchemaCreate,
    ) -> RoleDB:
        self.logger.debug(f"Creating {ITEM} {item}")
        async with self.db.get_session_maker()() as session:
            stmt = select(RoleDB).where(RoleDB.name == item.name)
            results = await session.execute(stmt)
            existing = results.scalar_one_or_none()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Role with name '{item.name}' already exists",
                )

            role = RoleDB(**item.model_dump())
            session.add(role)
            await session.commit()
            await session.refresh(role)
            return role

    async def get_by_id_with_user_count(
        self,
        role_id: int,
    ) -> RoleDB | None:
        self.logger.debug(f"Get {ITEM} by id:{role_id} with user_count")
        async with self.db.get_session_maker()() as session:
            stmt = select(RoleDB).where(RoleDB.id == role_id)
            results = await session.execute(stmt)
            role = results.scalar_one_or_none()

            if role is None:
                return None

            count_stmt = (
                select(func.count()).select_from(UserRoleDB).where(UserRoleDB.role_id == role_id)
            )
            count_result = await session.execute(count_stmt)
            user_count = count_result.scalar() or 0

            role.user_count = user_count
            return role

    async def update(
        self,
        item_id: int,
        item: RoleSchemaUpdate,
        **kwargs,
    ) -> RoleDB:
        self.logger.debug(f"Update {ITEM} id:{item_id}")
        async with self.db.get_session_maker()() as session:
            stmt = select(RoleDB).where(RoleDB.id == item_id)
            results = await session.execute(stmt)
            role = results.scalar_one_or_none()

            if role is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {item_id} not found",
                )

            update_data = item.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(role, field, value)

            await session.commit()
            await session.refresh(role)
            return role

    async def delete(
        self,
        item_id: int,
    ) -> None:
        self.logger.debug(f"Delete {ITEM} id:{item_id}")
        async with self.db.get_session_maker()() as session:
            stmt = select(RoleDB).options(selectinload(RoleDB.users)).where(RoleDB.id == item_id)
            results = await session.execute(stmt)
            role = results.scalar_one_or_none()

            if role is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {item_id} not found",
                )

            if role.users:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete role with assigned users. Remove users from role first.",
                )

            await session.delete(role)
            await session.commit()

    @handle_service_exceptions(
        item_name=ITEM,
        operation="searching roles with pagination",
        return_value_on_not_found=None,
    )
    async def search_roles_with_pagination(
        self,
        search_query: str | None = None,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "name",
        order_by_two: str = "id",
        ascending: bool = True,
    ) -> PaginatedRoleResponse:
        self.logger.debug(
            f"Search {ITEM}: query={search_query}, skip={skip}, limit={limit}, "
            f"order_by={order_by}, order_by_two={order_by_two}"
        )

        async with self.db.get_session_maker()() as session:
            base_query = select(RoleDB)

            base_query = await self._apply_search_filters(
                base_query,
                [(RoleDB, "name")],
                search_query,
            )

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await session.execute(count_stmt)
            total_items = count_result.scalar() or 0

            order_expr, order_expr_two = await self._build_order_expressions(
                RoleDB, order_by, order_by_two, ascending, RoleDB.name, RoleDB.id
            )

            data_query = base_query.order_by(order_expr, order_expr_two).offset(skip).limit(limit)
            result = await session.execute(data_query)
            roles = result.scalars().all()

            role_ids = [role.id for role in roles]
            user_counts = {}

            if role_ids:
                count_stmt = (
                    select(UserRoleDB.role_id, func.count(UserRoleDB.user_id).label("user_count"))
                    .where(UserRoleDB.role_id.in_(role_ids))
                    .group_by(UserRoleDB.role_id)
                )
                count_results = await session.execute(count_stmt)
                for row in count_results.all():
                    user_counts[row.role_id] = row.user_count

            roles_with_count = [
                RoleSchema(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    user_count=user_counts.get(role.id, 0),
                )
                for role in roles
            ]

            return PaginatedRoleResponse(
                data=roles_with_count,
                metadata=PaginationMetadata(
                    **await self._calculate_pagination_metadata(total_items, skip, limit),
                ),
            )
