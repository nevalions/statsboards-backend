"""User domain database service."""


from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.auth.security import get_password_hash, verify_password
from src.core.models import (
    BaseServiceDB,
    RoleDB,
    UserDB,
    UserRoleDB,
    handle_service_exceptions,
)
from src.core.models.base import Database
from src.logging_config import get_logger

from .schemas import UserSchemaCreate, UserSchemaUpdate

ITEM = "USER"


class UserServiceDB(BaseServiceDB):
    def __init__(self, database: Database) -> None:
        super().__init__(database, UserDB)
        self.logger = get_logger("backend_logger_UserServiceDB", self)
        self.logger.debug("Initialized UserServiceDB")

    @handle_service_exceptions(item_name=ITEM, operation="creating")
    async def create(self, item: UserSchemaCreate) -> UserDB:
        """Create a new user with hashed password.

        Args:
            item: User creation schema.

        Returns:
            UserDB: Created user.
        """
        item_dict = item.model_dump()
        item_dict["hashed_password"] = get_password_hash(item_dict.pop("password"))

        user = UserDB(**item_dict)
        async with self.db.async_session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    async def get_by_username(self, username: str) -> UserDB | None:
        """Get user by username.

        Args:
            username: Username to search for.

        Returns:
            UserDB | None: User if found, None otherwise.
        """
        self.logger.debug(f"Get {ITEM} by username:{username}")
        async with self.db.async_session() as session:
            stmt = select(UserDB).where(UserDB.username == username)
            results = await session.execute(stmt)
            return results.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserDB | None:
        """Get user by email.

        Args:
            email: Email to search for.

        Returns:
            UserDB | None: User if found, None otherwise.
        """
        self.logger.debug(f"Get {ITEM} by email:{email}")
        async with self.db.async_session() as session:
            stmt = select(UserDB).where(UserDB.email == email)
            results = await session.execute(stmt)
            return results.scalar_one_or_none()

    async def get_by_id_with_roles(self, user_id: int) -> UserDB | None:
        """Get user by ID with roles loaded.

        Args:
            user_id: User ID.

        Returns:
            UserDB | None: User if found, None otherwise.
        """
        self.logger.debug(f"Get {ITEM} by id:{user_id} with roles")
        async with self.db.async_session() as session:
            stmt = (
                select(UserDB)
                .where(UserDB.id == user_id)
                .options(selectinload(UserDB.roles).joinedload(UserRoleDB.role))
            )
            results = await session.execute(stmt)
            return results.scalar_one_or_none()

    async def update(
        self,
        item_id: int,
        item: UserSchemaUpdate,
        **kwargs,
    ) -> UserDB | None:
        """Update user information.

        Args:
            item_id: User ID to update.
            item: User update schema.
            **kwargs: Additional keyword arguments.

        Returns:
            UserDB: Updated user.

        Raises:
            HTTPException: If user not found.
        """
        self.logger.debug(f"Update {ITEM} id:{item_id}")
        async with self.db.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == item_id)
            results = await session.execute(stmt)
            user = results.scalar_one_or_none()

            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {item_id} not found",
                )

            update_data = item.model_dump(exclude_unset=True)

            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

            for field, value in update_data.items():
                setattr(user, field, value)

            await session.commit()
            await session.refresh(user)
            return user

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> UserDB:
        """Change user password.

        Args:
            user_id: User ID.
            old_password: Old password for verification.
            new_password: New password to set.

        Returns:
            UserDB: Updated user.

        Raises:
            HTTPException: If user not found or old password is incorrect.
        """
        self.logger.debug(f"Change password for {ITEM} id:{user_id}")
        async with self.db.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == user_id)
            results = await session.execute(stmt)
            user = results.scalar_one_or_none()

            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {user_id} not found",
                )

            if not verify_password(old_password, user.hashed_password):
                raise HTTPException(
                    status_code=400,
                    detail="Incorrect password",
                )

            user.hashed_password = get_password_hash(new_password)
            await session.commit()
            await session.refresh(user)
            return user

    async def assign_role(
        self,
        user_id: int,
        role_id: int,
    ) -> UserRoleDB:
        """Assign a role to a user.

        Args:
            user_id: User ID.
            role_id: Role ID.

        Returns:
            UserRoleDB: Created user-role relationship.

        Raises:
            HTTPException: If user or role not found, or relationship already exists.
        """
        self.logger.debug(f"Assign role {role_id} to {ITEM} id:{user_id}")
        async with self.db.async_session() as session:
            stmt = select(UserDB).where(UserDB.id == user_id)
            results = await session.execute(stmt)
            user = results.scalar_one_or_none()

            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ITEM} with id {user_id} not found",
                )

            stmt = select(RoleDB).where(RoleDB.id == role_id)
            results = await session.execute(stmt)
            role = results.scalar_one_or_none()

            if role is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Role with id {role_id} not found",
                )

            stmt = select(UserRoleDB).where(
                UserRoleDB.user_id == user_id,
                UserRoleDB.role_id == role_id,
            )
            results = await session.execute(stmt)
            existing = results.scalar_one_or_none()

            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"User already has role {role.name}",
                )

            user_role = UserRoleDB(user_id=user_id, role_id=role_id)
            session.add(user_role)
            await session.commit()
            await session.refresh(user_role)
            return user_role

    async def remove_role(
        self,
        user_id: int,
        role_id: int,
    ) -> None:
        """Remove a role from a user.

        Args:
            user_id: User ID.
            role_id: Role ID.

        Raises:
            HTTPException: If relationship not found.
        """
        self.logger.debug(f"Remove role {role_id} from {ITEM} id:{user_id}")
        async with self.db.async_session() as session:
            stmt = select(UserRoleDB).where(
                UserRoleDB.user_id == user_id,
                UserRoleDB.role_id == role_id,
            )
            results = await session.execute(stmt)
            user_role = results.scalar_one_or_none()

            if user_role is None:
                raise HTTPException(
                    status_code=404,
                    detail="User does not have this role",
                )

            await session.delete(user_role)
            await session.commit()

    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> UserDB | None:
        """Authenticate a user by username and password.

        Args:
            username: Username.
            password: Plain text password.

        Returns:
            UserDB | None: User if authentication successful, None otherwise.
        """
        self.logger.debug(f"Authenticate {ITEM} username:{username}")
        user = await self.get_by_username(username)

        if user is None or not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="User account is inactive",
            )

        return user
