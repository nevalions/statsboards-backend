"""Test user views/endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.auth.security import create_access_token, get_password_hash
from src.core.models import UserDB
from src.core.models.base import Database
from src.users.schemas import UserSchemaCreate


@pytest.fixture
async def test_user(test_db: Database):
    """Create a test user."""
    async with test_db.async_session() as db_session:
        user_data = UserSchemaCreate(
            username="test_view_user",
            email="test_view@example.com",
            password="SecurePass123!",
        )
        user = UserDB(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        yield user

        await db_session.delete(user)
        await db_session.commit()


class TestUserViews:
    """Test user API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: TestClient):
        """Test successful user registration."""
        user_data = {
            "username": "new_test_user",
            "email": "new_test@example.com",
            "password": "SecurePass123!",
        }

        response = await client.post("/api/users/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["username"] == "new_test_user"

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: TestClient, test_user):
        """Test registration fails with duplicate username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "SecurePass123!",
        }

        response = await client.post("/api/users/register", json=user_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: TestClient, test_user):
        """Test /users/me endpoint with valid token."""
        from src.auth.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})

        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: TestClient):
        """Test /users/me endpoint without token returns 401."""
        response = await client.get("/api/users/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_authenticated(self, client: TestClient, test_user):
        """Test updating current user profile."""
        from src.auth.security import create_access_token

        token = create_access_token(data={"sub": str(test_user.id)})

        update_data = {"email": "updated@example.com"}
        response = await client.put(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

    @pytest.mark.asyncio
    async def test_update_me_unauthorized(self, client: TestClient):
        """Test updating profile without token returns 401."""
        update_data = {"email": "updated@example.com"}
        response = await client.put("/api/users/me", json=update_data)

        assert response.status_code == 401
