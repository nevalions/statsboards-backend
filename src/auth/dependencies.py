"""Authentication and authorization dependencies for FastAPI."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.auth.security import decode_access_token
from src.core.dependencies import UserService
from src.core.models import UserDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserService,
) -> UserDB:
    """Dependency to get current authenticated user from JWT token.

    Args:
        token: JWT token from OAuth2 scheme.
        user_service: User service instance.

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

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

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


def require_roles(*required_roles: str):
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

    async def role_checker(
        current_user: Annotated[UserDB, Depends(get_current_user)],
        user_service: UserService,
    ) -> UserDB:
        """Check if user has required roles.

        Args:
            current_user: Current authenticated user.
            user_service: User service instance.

        Returns:
            UserDB: Current user if they have required roles.

        Raises:
            HTTPException: If user lacks required roles.
        """
        user = await user_service.get_by_id_with_roles(current_user.id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user_roles = {role.name for role in user.roles}

        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}",
            )

        return user

    return role_checker


CurrentUser = Annotated[UserDB, Depends(get_current_user)]
