"""User domain views/router."""

from typing import Annotated

from fastapi import Depends, HTTPException, Query

from src.auth.dependencies import CurrentUser, UserService, require_roles
from src.auth.schemas import UserRoleAssign
from src.core import BaseRouter
from src.core.models import UserDB
from src.logging_config import get_logger

from .schemas import (
    AdminPasswordChange,
    PaginatedUserResponse,
    UserChangePassword,
    UserSchema,
    UserSchemaCreate,
    UserSchemaUpdate,
)

ITEM = "USER"


class UserAPIRouter(BaseRouter[UserSchema, UserSchemaCreate, UserSchemaUpdate]):
    def __init__(self):
        super().__init__("/api/users", ["users"], None)
        self.logger = get_logger("backend_logger_UserAPIRouter", self)
        self.logger.debug("Initialized UserAPIRouter")

    def route(self):
        router = super().route()

        @router.post(
            "/register",
            response_model=UserSchema,
            summary="Register a new user",
            description="Creates a new user account. Returns created user with their ID.",
            responses={
                200: {"description": "User created successfully"},
                400: {"description": "Bad request - validation error or user already exists"},
                500: {"description": "Internal server error"},
            },
        )
        async def register_user(user_service: UserService, user_data: UserSchemaCreate):
            """Register a new user."""
            self.logger.debug(f"Register user endpoint got data: {user_data}")

            existing_user = await user_service.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username already exists",
                )

            existing_user = await user_service.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists",
                )

            new_user = await user_service.create(user_data)
            user = await user_service.get_by_id_with_roles(new_user.id)
            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.get(
            "/me",
            response_model=UserSchema,
            summary="Get current user profile",
            description="Returns profile of currently authenticated user.",
        )
        async def get_current_user_profile(
            user_service: UserService, current_user: CurrentUser
        ) -> UserSchema:
            """Get current user profile."""
            self.logger.debug(f"Get current user profile: {current_user.id}")

            user = await user_service.get_by_id_with_roles(current_user.id)
            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )

            roles = [role.name for role in user.roles]

            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.put(
            "/me",
            response_model=UserSchema,
            summary="Update current user profile",
            description="Updates profile of currently authenticated user.",
        )
        async def update_current_user_profile(
            user_service: UserService,
            user_data: UserSchemaUpdate,
            current_user: CurrentUser,
        ) -> UserSchema:
            """Update current user profile."""
            self.logger.debug(f"Update current user profile: {current_user.id}")

            updated_user = await user_service.update(current_user.id, user_data)
            user = await user_service.get_by_id_with_roles(updated_user.id)

            roles = [role.name for role in user.roles]

            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.post(
            "/me/change-password",
            summary="Change own password",
            description="Change password for current user. Requires verification of current password.",
            responses={
                200: {"description": "Password changed successfully"},
                400: {"description": "Incorrect current password"},
                401: {"description": "Unauthorized"},
            },
        )
        async def change_own_password(
            user_service: UserService,
            password_data: UserChangePassword,
            current_user: CurrentUser,
        ):
            """Change own password."""
            self.logger.debug(f"Change own password for user: {current_user.id}")
            await user_service.change_password(
                current_user.id,
                password_data.old_password,
                password_data.new_password,
            )
            return {"message": "Password changed successfully"}

        @router.post(
            "/{user_id}/roles",
            response_model=UserSchema,
            summary="Assign role to user",
            description="Assign a role to a user. Requires admin role.",
            responses={
                200: {"description": "Role assigned successfully"},
                400: {"description": "Bad request - user already has this role"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User or role not found"},
            },
        )
        async def assign_role_to_user(
            user_service: UserService,
            user_id: int,
            role_assign: UserRoleAssign,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Assign a role to a user."""
            self.logger.debug(f"Assign role {role_assign.role_id} to user {user_id}")

            await user_service.assign_role(user_id, role_assign.role_id)
            user = await user_service.get_by_id_with_roles(user_id)

            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )

            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.delete(
            "/{user_id}/roles/{role_id}",
            response_model=UserSchema,
            summary="Remove role from user",
            description="Remove a role from a user. Requires admin role.",
            responses={
                200: {"description": "Role removed successfully"},
                400: {"description": "Bad request - user does not have this role"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User or role not found"},
            },
        )
        async def remove_role_from_user(
            user_service: UserService,
            user_id: int,
            role_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Remove a role from a user."""
            self.logger.debug(f"Remove role {role_id} from user {user_id}")

            await user_service.remove_role(user_id, role_id)
            user = await user_service.get_by_id_with_roles(user_id)

            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )

            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.get(
            "/{user_id}/roles",
            summary="Get user roles",
            description="Returns the roles for a user. Requires admin role.",
            responses={
                200: {"description": "Roles found"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User not found"},
            },
        )
        async def get_user_roles(
            user_service: UserService,
            user_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Get user roles."""
            self.logger.debug(f"Get roles for user: {user_id}")

            user = await user_service.get_by_id_with_roles(user_id)
            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )

            return {"roles": [role.name for role in user.roles] if user.roles else []}

        @router.get(
            "/search",
            response_model=PaginatedUserResponse,
            summary="Search users with pagination",
            description="Search users by username. Supports pagination, ordering (username, is_online, etc.), role filtering, and online status filtering.",
        )
        async def search_users_endpoint(
            user_service: UserService,
            page: int = Query(1, ge=1, description="Page number (1-based)"),
            items_per_page: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
            order_by: str = Query("username", description="First sort column"),
            order_by_two: str = Query("id", description="Second sort column"),
            ascending: bool = Query(True, description="Sort order (true=asc, false=desc)"),
            search: str | None = Query(None, description="Search query for text search"),
            role_names: list[str] | None = Query(None, description="Filter users by role names"),
            is_online: bool | None = Query(None, description="Filter users by online status"),
        ):
            self.logger.debug(
                f"Search users: page={page}, items_per_page={items_per_page}, "
                f"order_by={order_by}, order_by_two={order_by_two}, ascending={ascending}, search={search}, role_names={role_names}, is_online={is_online}"
            )
            skip = (page - 1) * items_per_page
            response = await user_service.search_users_with_pagination(
                search_query=search,
                skip=skip,
                limit=items_per_page,
                order_by=order_by,
                order_by_two=order_by_two,
                ascending=ascending,
                role_names=role_names,
                is_online=is_online,
            )
            return response

        @router.get(
            "/{user_id}",
            response_model=UserSchema,
            summary="Get user by ID with roles",
            description="Returns user profile with their roles. Requires admin role.",
            responses={
                200: {"description": "User found"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User not found"},
            },
        )
        async def get_user_by_id(
            user_service: UserService,
            user_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Get user by ID with roles."""
            self.logger.debug(f"Get user by id: {user_id}")

            user = await user_service.get_by_id_with_roles(user_id)
            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail="User not found",
                )

            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.put(
            "/{user_id}",
            response_model=UserSchema,
            summary="Update user by ID",
            description="Updates user information (email, is_active). Requires admin role.",
            responses={
                200: {"description": "User updated successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User not found"},
                400: {"description": "Bad request - validation error"},
            },
        )
        async def update_user_by_id(
            user_service: UserService,
            user_id: int,
            user_data: UserSchemaUpdate,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Update user by ID."""
            self.logger.debug(f"Update user by id: {user_id}")

            updated_user = await user_service.update(user_id, user_data)
            user = await user_service.get_by_id_with_roles(updated_user.id)

            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.post(
            "/{user_id}/change-password",
            response_model=UserSchema,
            summary="Admin change user password",
            description="Changes a user's password. Does not require old password. Requires admin role.",
            responses={
                200: {"description": "Password changed successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User not found"},
            },
        )
        async def admin_change_password(
            user_service: UserService,
            user_id: int,
            password_data: AdminPasswordChange,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Admin change user password."""
            self.logger.debug(f"Admin change password for user: {user_id}")

            updated_user = await user_service.admin_change_password(
                user_id, password_data.new_password
            )
            user = await user_service.get_by_id_with_roles(updated_user.id)

            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
                created=user.created,
                last_online=user.last_online,
                is_online=user.is_online,
            )

        @router.delete(
            "/{user_id}",
            summary="Delete user by ID",
            description="Delete a user by ID. Requires admin role.",
            responses={
                200: {"description": "User deleted successfully"},
                401: {"description": "Unauthorized"},
                403: {"description": "Forbidden - requires admin role"},
                404: {"description": "User not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_user_by_id(
            user_service: UserService,
            user_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ):
            """Delete user by ID."""
            self.logger.debug(f"Delete user by id: {user_id}")

            await user_service.delete(user_id)
            return {"detail": f"{ITEM} {user_id} deleted successfully"}

        @router.delete(
            "/me",
            summary="Delete current user",
            description="Delete currently authenticated user's account.",
            responses={
                200: {"description": "User deleted successfully"},
                401: {"description": "Unauthorized"},
                404: {"description": "User not found"},
                500: {"description": "Internal server error"},
            },
        )
        async def delete_current_user(user_service: UserService, current_user: CurrentUser):
            """Delete current user."""
            self.logger.debug(f"Delete current user: {current_user.id}")

            await user_service.delete(current_user.id)
            return {"detail": f"{ITEM} deleted successfully"}

        return router


def get_user_router():
    """Get user router instance."""
    return UserAPIRouter().route()


api_user_router = get_user_router()
