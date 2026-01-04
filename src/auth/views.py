"""Authentication router."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import CurrentUser
from src.auth.schemas import Token
from src.core.service_registry import get_service_registry
from src.logging_config import get_logger
from src.users.db_services import UserServiceDB
from src.users.schemas import UserSchema


class AuthRouter:
    def __init__(self):
        self.logger = get_logger("backend_logger_AuthRouter", self)
        self.logger.debug("Initialized AuthRouter")
        self.router = APIRouter(prefix="/api/auth", tags=["auth"])

    def route(self):
        @self.router.post(
            "/login",
            response_model=Token,
            summary="Login user",
            description="Authenticate a user with username and password. Returns JWT access token.",
            responses={
                200: {"description": "Login successful"},
                401: {"description": "Invalid credentials"},
                500: {"description": "Internal server error"},
            },
        )
        async def login_for_access_token(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        ) -> Token:
            """Authenticate user and return JWT token."""
            self.logger.debug(f"Login attempt for username: {form_data.username}")

            registry = get_service_registry()
            user_service = UserServiceDB(registry.database)

            user = await user_service.authenticate(
                form_data.username,
                form_data.password,
            )

            if user is None:
                self.logger.warning(f"Failed login attempt for username: {form_data.username}")
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            from src.auth.security import create_access_token

            access_token = create_access_token(data={"sub": str(user.id)})
            self.logger.info(f"User {user.username} logged in successfully")

            return Token(access_token=access_token, token_type="bearer")

        @self.router.get(
            "/me",
            response_model=UserSchema,
            summary="Get current user",
            description="Returns currently authenticated user's profile.",
        )
        async def get_current_user_info(current_user: CurrentUser) -> UserSchema:
            """Get current user profile."""
            self.logger.debug(f"Get current user info: {current_user.id}")

            registry = get_service_registry()
            user_service = UserServiceDB(registry.database)
            user = await user_service.get_by_id_with_roles(current_user.id)

            if user is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            roles = [role.role.name for role in user.roles]

            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                is_active=user.is_active,
                person_id=user.person_id,
                roles=roles,
            )

        return self.router


api_auth_router = AuthRouter().route()
