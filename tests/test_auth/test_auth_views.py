"""Test auth views/endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.auth.security import create_access_token
from src.core.models import RoleDB, UserDB, UserRoleDB
from src.core.models.base import Database
from src.users.db_services import UserServiceDB
from src.users.schemas import UserSchemaCreate


@pytest.fixture
async def test_user_with_role(test_db: Database):
    """Create a test user with a role."""
    from src.auth.security import get_password_hash

    async with test_db.async_session() as db_session:
        role = RoleDB(name="test_role", description="Test role")
        db_session.add(role)
        await db_session.commit()

        user_data = UserSchemaCreate(
            username="test_api_user",
            email="test_api@example.com",
            password="SecurePass123!",
        )
        user = UserDB(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
        )
        db_session.add(user)
        await db_session.commit()

        db_session.add(UserRoleDB(user_id=user.id, role_id=role.id))
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(user, ["roles"])

        yield user

        await db_session.delete(user)
        await db_session.delete(role)
        await db_session.commit()

        user_data = UserSchemaCreate(
            username="test_api_user",
            email="test_api@example.com",
            password="SecurePass123!",
        )
        user = UserDB(**user_data.model_dump())
        user.hashed_password = user_data.password
        db_session.add(user)
        await db_session.commit()

        db_session.add(UserRoleDB(user_id=user.id, role_id=role.id))
        await db_session.commit()

        await db_session.refresh(user)
        await db_session.refresh(user, ["roles"])

        yield user

        await db_session.delete(user)
        await db_session.delete(role)
        await db_session.commit()


class TestAuthViews:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: TestClient, test_db):
        """Test successful login returns token."""
        user_data = UserSchemaCreate(
            username="testuser_login",
            email="testuser_login@example.com",
            password="SecurePass123!",
        )

        service = UserServiceDB(test_db)
        user = await service.create(user_data)

        response = await client.post(
            "/api/auth/login",
            data={"username": "testuser_login", "password": "SecurePass123!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: TestClient):
        """Test login fails with invalid credentials."""
        response = await client.post(
            "/api/auth/login",
            data={"username": "wronguser", "password": "wrongpass"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: TestClient, test_user_with_role):
        """Test /me endpoint with valid token."""
        token = create_access_token(data={"sub": str(test_user_with_role.id)})

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_with_role.id
        assert data["username"] == "test_api_user"

    @pytest.mark.asyncio
    async def test_me_no_token(self, client: TestClient):
        """Test /me endpoint without token returns 401."""
        response = await client.get("/api/auth/me")

        assert response.status_code == 401
