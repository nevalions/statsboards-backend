"""User domain views/router."""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.auth.dependencies import CurrentUser, require_roles
from src.auth.schemas import UserRoleAssign
from src.core import BaseRouter
from src.core.models import UserDB
from src.core.service_registry import get_service_registry
from src.logging_config import get_logger

from .db_services import UserServiceDB
from .schemas import UserSchema, UserSchemaCreate, UserSchemaUpdate

ITEM = "USER"


class UserAPIRouter(BaseRouter[UserSchema, UserSchemaCreate, UserSchemaUpdate]):
    def __init__(self, service: UserServiceDB):
        super().__init__("/api/users", ["users"], service)
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
        async def register_user(user_data: UserSchemaCreate):
            """Register a new user."""
            self.logger.debug(f"Register user endpoint got data: {user_data}")

            existing_user = await self.service.get_by_username(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Username already exists",
                )

            existing_user = await self.service.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists",
                )

            new_user = await self.service.create(user_data)
            user = await self.service.get_by_id_with_roles(new_user.id)
            roles = [role.name for role in user.roles] if user.roles else []
            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
            )

        @router.get(
            "/me",
            response_model=UserSchema,
            summary="Get current user profile",
            description="Returns profile of currently authenticated user.",
        )
        async def get_current_user_profile(current_user: CurrentUser) -> UserSchema:
            """Get current user profile."""
            self.logger.debug(f"Get current user profile: {current_user.id}")

            user = await self.service.get_by_id_with_roles(current_user.id)
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
            )

        @router.put(
            "/me",
            response_model=UserSchema,
            summary="Update current user profile",
            description="Updates profile of currently authenticated user.",
        )
        async def update_current_user_profile(
            user_data: UserSchemaUpdate,
            current_user: CurrentUser,
        ) -> UserSchema:
            """Update current user profile."""
            self.logger.debug(f"Update current user profile: {current_user.id}")

            updated_user = await self.service.update(current_user.id, user_data)
            user = await self.service.get_by_id_with_roles(updated_user.id)

            roles = [role.name for role in user.roles]

            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
            )

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
            user_id: int,
            role_assign: UserRoleAssign,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Assign a role to a user."""
            self.logger.debug(f"Assign role {role_assign.role_id} to user {user_id}")

            await self.service.assign_role(user_id, role_assign.role_id)
            user = await self.service.get_by_id_with_roles(user_id)

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
            user_id: int,
            role_id: int,
            _: Annotated[UserDB, Depends(require_roles("admin"))],
        ) -> UserSchema:
            """Remove a role from a user."""
            self.logger.debug(f"Remove role {role_id} from user {user_id}")

            await self.service.remove_role(user_id, role_id)
            user = await self.service.get_by_id_with_roles(user_id)

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
            )

        return router


def get_user_router():
    """Get user router instance."""
    from src.core.models import db

    try:
        registry = get_service_registry()
        service = UserServiceDB(registry.database)
        return UserAPIRouter(service).route()
    except RuntimeError:
        return UserAPIRouter(UserServiceDB(db)).route()


api_user_router = get_user_router()
