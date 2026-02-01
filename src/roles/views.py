from typing import Annotated

from fastapi import Depends, HTTPException, Query

from src.auth.dependencies import require_roles
from src.core import BaseRouter
from src.core.models import RoleDB
from src.core.service_registry import get_service_registry
from src.logging_config import get_logger

from .db_services import RoleServiceDB
from .schemas import PaginatedRoleResponse, RoleSchema, RoleSchemaCreate, RoleSchemaUpdate

ITEM = "ROLE"


class RoleAPIRouter(BaseRouter[RoleSchema, RoleSchemaCreate, RoleSchemaUpdate]):
    def __init__(self, service: RoleServiceDB | None = None, service_name: str | None = None):
        super().__init__("/api/roles", ["roles"], service, service_name=service_name)
        self.logger = get_logger("RoleAPIRouter", self)
        self.logger.debug("Initialized RoleAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/",
            response_model=RoleSchema,
            summary="Create role",
            description="Create a new role. Requires admin role.",
            responses={
                200: {"description": "Role created successfully"},
                400: {"description": "Bad request - role name already exists"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                500: {"description": "Internal server error"},
            },
        )
        async def create_role_endpoint(
            role_data: RoleSchemaCreate,
            _: Annotated[RoleDB, Depends(require_roles("admin"))],
        ) -> RoleSchema:
            self.logger.debug(f"Create role endpoint: {role_data}")
            new_role = await self.loaded_service.create(role_data)
            role = await self.loaded_service.get_by_id_with_user_count(new_role.id)
            if role is None:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve created role",
                )
            return RoleSchema(
                id=role.id,
                name=role.name,
                description=role.description,
                user_count=role.user_count,
            )

        @router.put(
            "/{item_id}/",
            response_model=RoleSchema,
            summary="Update role",
            description="Update role description. Requires admin role.",
            responses={
                200: {"description": "Role updated successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Role not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def update_role_endpoint(
            item_id: int,
            role_data: RoleSchemaUpdate,
            _: Annotated[RoleDB, Depends(require_roles("admin"))],
        ) -> RoleSchema:
            self.logger.debug(f"Update role endpoint id:{item_id}")
            updated_role = await self.loaded_service.update(item_id, role_data)
            role = await self.loaded_service.get_by_id_with_user_count(updated_role.id)
            if role is None:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to retrieve updated role",
                )
            return RoleSchema(
                id=role.id,
                name=role.name,
                description=role.description,
                user_count=role.user_count,
            )

        @router.get(
            "/id/{item_id}/",
            response_model=RoleSchema,
            summary="Get role by ID",
            description="Get a role by ID with user count.",
            responses={
                200: {"description": "Role retrieved successfully"},
                404: {"description": "Role not found"},
            },
        )
        async def get_role_by_id_endpoint(item_id: int) -> RoleSchema:
            self.logger.debug(f"Get role by id endpoint: {item_id}")
            role = await self.loaded_service.get_by_id_with_user_count(item_id)
            if role is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {item_id} not found",
                )
            return RoleSchema(
                id=role.id,
                name=role.name,
                description=role.description,
                user_count=role.user_count,
            )

        @router.get(
            "/paginated",
            response_model=PaginatedRoleResponse,
            summary="Search roles with pagination",
            description="Search roles by name with pagination and standard query parameters",
        )
        async def search_roles_paginated_endpoint(
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("name", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for role name"),
        ):
            self.logger.debug(
                f"Search roles paginated: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}"
            )
            skip = (page - 1) * items_per_page
            response = await self.loaded_service.search_roles_with_pagination(
                search_query=search,
                skip=skip,
                limit=items_per_page,
                order_by=order_by,
                order_by_two=order_by_two,
                ascending=ascending,
            )
            return response

        @router.delete(
            "/id/{model_id}",
            summary="Delete role",
            description="Delete a role. Requires admin role. Cannot delete if role is assigned to users.",
            responses={
                200: {"description": "Role deleted successfully"},
                400: {"description": "Bad request - role is assigned to users"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "Role not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_role_endpoint(
            model_id: int,
            _: Annotated[RoleDB, Depends(require_roles("admin"))],
        ):
            self.logger.debug(f"Delete role endpoint id:{model_id}")
            await self.loaded_service.delete(model_id)
            return {"detail": f"{ITEM} {model_id} deleted successfully"}

        return router


def get_role_router():
    from src.core.models import db

    try:
        registry = get_service_registry()
        service = RoleServiceDB(registry.database)
        return RoleAPIRouter(service).route()
    except RuntimeError:
        return RoleAPIRouter(RoleServiceDB(db)).route()


api_role_router = get_role_router()
