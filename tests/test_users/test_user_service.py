"""Test user service database operations."""

import pytest

from src.auth.security import verify_password
from src.core.models.base import Database
from src.users.db_services import UserServiceDB
from src.users.schemas import UserSchemaCreate


class TestUserServiceDB:
    """Test UserServiceDB operations."""

    @pytest.mark.asyncio
    async def test_create_user_with_default_role(self, test_db: Database):
        """Test creating a user with default role."""
        user_data = UserSchemaCreate(
            username="testuser1",
            email="test1@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        user = await service.create(user_data)

        assert user.id is not None
        assert user.username == "testuser1"
        assert user.email == "test1@example.com"
        assert user.is_active is True
        assert verify_password("SecurePass123!", user.hashed_password)

    @pytest.mark.asyncio
    async def test_create_user_with_person(self, test_db: Database):
        """Test creating a user linked to PersonDB."""
        from src.core.models import PersonDB

        async with test_db.async_session() as session:
            person = PersonDB(
                person_eesl_id=2000,
                first_name="Test",
                second_name="Person",
            )
            session.add(person)
            await session.flush()
            await session.refresh(person)

        user_data = UserSchemaCreate(
            username="testuser2",
            email="test2@example.com",
            password="SecurePass123!",
            person_id=person.id,
        )

        service = UserServiceDB(test_db)
        user = await service.create(user_data)

        assert user.person_id == person.id
        assert user.username == "testuser2"

    @pytest.mark.asyncio
    async def test_authenticate_success(self, test_db: Database):
        """Test user authentication with correct credentials."""
        user_data = UserSchemaCreate(
            username="testuser3",
            email="test3@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        await service.create(user_data)

        authenticated_user = await service.authenticate("testuser3", "SecurePass123!")

        assert authenticated_user is not None
        assert authenticated_user.username == "testuser3"

    @pytest.mark.asyncio
    async def test_authenticate_wrong_password(self, test_db: Database):
        """Test authentication fails with wrong password."""
        user_data = UserSchemaCreate(
            username="testuser4",
            email="test4@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        await service.create(user_data)

        authenticated_user = await service.authenticate("testuser4", "WrongPass!")

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, test_db: Database):
        """Test authentication fails with nonexistent user."""
        service = UserServiceDB(test_db)

        authenticated_user = await service.authenticate("nonexistent", "password")

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_get_by_email(self, test_db: Database):
        """Test getting user by email."""
        user_data = UserSchemaCreate(
            username="testuser5",
            email="test5@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        created_user = await service.create(user_data)

        fetched_user = await service.get_by_email("test5@example.com")

        assert fetched_user is not None
        assert fetched_user.id == created_user.id
        assert fetched_user.email == "test5@example.com"

    @pytest.mark.asyncio
    async def test_change_password(self, test_db: Database):
        """Test changing user password."""
        user_data = UserSchemaCreate(
            username="testuser7",
            email="test7@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        user = await service.create(user_data)

        updated_user = await service.change_password(user.id, "SecurePass123!", "NewSecurePass456!")

        assert verify_password("NewSecurePass456!", updated_user.hashed_password)
        assert not verify_password("SecurePass123!", updated_user.hashed_password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(self, test_db: Database):
        """Test changing password with wrong old password fails."""
        from fastapi import HTTPException

        user_data = UserSchemaCreate(
            username="testuser8",
            email="test8@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        user = await service.create(user_data)

        with pytest.raises(HTTPException) as exc_info:
            await service.change_password(user.id, "WrongPass!", "NewSecurePass456!")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_online_and_is_online(self, test_db: Database):
        """Test heartbeat updates last_online timestamp and is_online flag."""
        from src.auth.security import get_password_hash
        from src.core.models import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="heartbeat_test",
                email="heartbeat@example.com",
                hashed_password=get_password_hash("password123"),
                is_online=False,
            )
            session.add(user)
            await session.flush()
            user_id = user.id

        service = UserServiceDB(test_db)
        await service.heartbeat(user_id)

        async with test_db.async_session() as session:
            from sqlalchemy import select

            stmt = select(UserDB).where(UserDB.id == user_id)
            result = await session.execute(stmt)
            updated_user = result.scalar_one()

            assert updated_user.last_online is not None
            assert updated_user.is_online is True

    @pytest.mark.asyncio
    async def test_mark_stale_users_offline(self, test_db: Database):
        """Test marking stale users as offline."""
        from datetime import UTC, datetime, timedelta

        from src.auth.security import get_password_hash
        from src.core.models import UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="stale_user1",
                email="stale1@example.com",
                hashed_password=get_password_hash("password123"),
                is_online=True,
                last_online=datetime.now(UTC) - timedelta(minutes=5),
            )
            user2 = UserDB(
                username="stale_user2",
                email="stale2@example.com",
                hashed_password=get_password_hash("password123"),
                is_online=True,
                last_online=datetime.now(UTC) - timedelta(minutes=1),
            )
            user3 = UserDB(
                username="active_user",
                email="active@example.com",
                hashed_password=get_password_hash("password123"),
                is_online=True,
                last_online=datetime.now(UTC),
            )
            session.add_all([user1, user2, user3])
            await session.flush()

        count = await service.mark_stale_users_offline(timeout_minutes=2)

        assert count == 1

        async with test_db.async_session() as session:
            from sqlalchemy import select

            stmt = select(UserDB).where(UserDB.username == "stale_user1")
            result = await session.execute(stmt)
            stale_user = result.scalar_one()
            assert stale_user.is_online is False

            stmt = select(UserDB).where(UserDB.username == "stale_user2")
            result = await session.execute(stmt)
            recent_user = result.scalar_one()
            assert recent_user.is_online is True

            stmt = select(UserDB).where(UserDB.username == "active_user")
            result = await session.execute(stmt)
            active_user = result.scalar_one()
            assert active_user.is_online is True
