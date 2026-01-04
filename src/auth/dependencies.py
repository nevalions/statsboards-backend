"""Authentication and authorization dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.auth.security import decode_access_token
from src.core.models import UserDB, UserRoleDB, db
from src.core.service_registry import get_service_registry

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserDB:
    """Dependency to get current authenticated user from JWT token.

    Args:
        token: JWT token from OAuth2 scheme.

    Returns:
        UserDB: Current authenticated user.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    service_registry = get_service_registry()
    user_service = service_registry.get("user")
    if user_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User service not available",
        )

    user = await user_service.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[UserDB, Depends(get_current_user)],
) -> UserDB:
    """Dependency to get current active user.

    Args:
        current_user: Current authenticated user.

    Returns:
        UserDB: Current active user.

    Raises:
        HTTPException: If user is not active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    return current_user


async def require_roles(*required_roles: str):
    """Dependency factory to require specific user roles.

    Args:
        *required_roles: Required role names.

    Returns:
        Callable: FastAPI dependency that checks user roles.

    Example:
        @router.get("/admin/")
        async def admin_endpoint(
            user: Annotated[UserDB, Depends(require_roles("admin"))]
        ):
            ...
    """

    async def role_checker(current_user: Annotated[UserDB, Depends(get_current_user)]) -> UserDB:
        """Check if user has required roles.

        Args:
            current_user: Current authenticated user.

        Returns:
            UserDB: Current user if they have required roles.

        Raises:
            HTTPException: If user lacks required roles.
        """
        async with db.async_session() as session:
            stmt = (
                select(UserDB)
                .where(UserDB.id == current_user.id)
                .options(selectinload(UserDB.roles).joinedload(UserRoleDB.role))
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            user_roles = {role.role.name for role in user.roles}

            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(required_roles)}",
                )

            return user

    return role_checker


CurrentUser = Annotated[UserDB, Depends(get_current_user)]
