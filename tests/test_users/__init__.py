"""Test user service database operations."""

import pytest

from src.auth.security import get_password_hash, verify_password
from src.core.models import UserDB, db
from src.users.db_services import UserServiceDB
from src.users.schemas import UserSchemaCreate, UserSchemaUpdate


@pytest.fixture
async def test_user(session):
    """Create a test user."""
    async with db.async_session() as db_session:
        user_data = UserSchemaCreate(
            username="test_view_user",
            email="test_view@example.com",
            password="SecurePass123!",
        )
        user = UserDB(**user_data.model_dump())
        user.hashed_password = get_password_hash(user_data.password)
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        yield user

        await db_session.delete(user)


class TestUserServiceDB:
    """Test UserServiceDB operations."""

    @pytest.mark.asyncio
    async def test_create_user_with_default_role(
        self,
        user_factory,
        session,
    ):
        """Test creating a user with default role."""
        user_data = UserSchemaCreate(
            username="testuser1",
            email="test1@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        user = await service.create(user_data)

        assert user.id is not None
        assert user.username == "testuser1"
        assert user.email == "test1@example.com"
        assert user.is_active is True

        await session.rollback()

    @pytest.mark.asyncio
    async def test_create_user_with_person(self, session):
        """Test creating a user linked to PersonDB."""
        from tests.factories import PersonFactory

        person_data = PersonFactory.build()
        user_data = UserSchemaCreate(
            username="testuser2",
            email="test2@example.com",
            password="SecurePass123!",
            person_id=person_data.person_eesl_id,
        )

        service = UserServiceDB(db)
        user = await service.create(user_data)

        assert user.person_id is not None
        assert user.username == "testuser2"

        await session.rollback()

    @pytest.mark.asyncio
    async def test_authenticate_success(self, session):
        """Test user authentication with correct credentials."""
        user_data = UserSchemaCreate(
            username="testuser3",
            email="test3@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        await service.create(user_data)

        authenticated_user = await service.authenticate("testuser3", "SecurePass123!")

        assert authenticated_user is not None
        assert authenticated_user.username == "testuser3"

        await session.rollback()

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, session):
        """Test authentication fails with wrong password."""
        user_data = UserSchemaCreate(
            username="testuser4",
            email="test4@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        await service.create(user_data)

        authenticated_user = await service.authenticate("testuser4", "WrongPass!")

        assert authenticated_user is None

        await session.rollback()

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, session):
        """Test authentication fails with nonexistent user."""
        service = UserServiceDB(db)

        authenticated_user = await service.authenticate("nonexistent", "password")

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, session):
        """Test getting user by email."""
        user_data = UserSchemaCreate(
            username="testuser5",
            email="test5@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        created_user = await service.create(user_data)

        fetched_user = await service.get_by_email("test5@example.com")

        assert fetched_user is not None
        assert fetched_user.id == created_user.id
        assert fetched_user.email == "test5@example.com"

        await session.rollback()

    @pytest.mark.asyncio
    async def test_update_user_password(self, session):
        """Test updating user password."""
        user_data = UserSchemaCreate(
            username="testuser6",
            email="test6@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        user = await service.create(user_data)

        update_data = UserSchemaUpdate(password="NewSecurePass456!")
        updated_user = await service.update(user.id, update_data)

        assert verify_password("NewSecurePass456!", updated_user.hashed_password)
        assert not verify_password("SecurePass123!", updated_user.hashed_password)

        await session.rollback()

    @pytest.mark.asyncio
    async def test_change_password(self, session):
        """Test changing user password."""
        user_data = UserSchemaCreate(
            username="testuser7",
            email="test7@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        user = await service.create(user_data)

        updated_user = await service.change_password(user.id, "SecurePass123!", "NewSecurePass456!")

        assert verify_password("NewSecurePass456!", updated_user.hashed_password)
        assert not verify_password("SecurePass123!", updated_user.hashed_password)

        await session.rollback()

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, session):
        """Test changing password with wrong old password fails."""
        from fastapi import HTTPException

        user_data = UserSchemaCreate(
            username="testuser8",
            email="test8@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(db)
        user = await service.create(user_data)

        with pytest.raises(HTTPException) as exc_info:
            await service.change_password(user.id, "WrongPass!", "NewSecurePass456!")

        assert exc_info.value.status_code == 400

        await session.rollback()
