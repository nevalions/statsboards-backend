"""Test role views/endpoints."""

import pytest
from httpx import AsyncClient

from src.auth.security import create_access_token
from src.core.models import RoleDB, UserDB
from src.core.models.base import Database
from src.users.schemas import UserSchemaCreate


@pytest.fixture
async def test_role(test_db: Database):
    """Create a test role."""
    async with test_db.async_session() as db_session:
        role = RoleDB(name="test_role", description="Test role description")
        db_session.add(role)
        await db_session.flush()
        await db_session.refresh(role)

        yield role

        await db_session.delete(role)


@pytest.fixture
async def test_admin_user(test_db: Database):
    """Create a test admin user."""
    async with test_db.async_session() as db_session:
        from src.auth.security import get_password_hash

        role = RoleDB(name="admin", description="Admin role")
        db_session.add(role)
        await db_session.flush()
        await db_session.refresh(role)

        user_data = UserSchemaCreate(
            username="test_admin",
            email="admin@example.com",
            password="SecurePass123!",
        )
        user_obj = UserDB(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
        )
        user_obj.roles = [role]
        db_session.add(user_obj)
        await db_session.flush()
        await db_session.refresh(user_obj)

        yield user_obj

        await db_session.delete(user_obj)
        await db_session.delete(role)


@pytest.fixture
async def admin_token(test_admin_user: UserDB) -> str:
    """Get admin token for authenticated requests."""
    return create_access_token(data={"sub": str(test_admin_user.id)})


class TestRoleViews:
    """Test role API endpoints."""

    @pytest.mark.asyncio
    async def test_create_role_success(self, client: AsyncClient, admin_token: str):
        """Test successful role creation."""
        role_data = {
            "name": "moderator",
            "description": "Moderator role",
        }

        response = await client.post(
            "/api/roles/",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "moderator"
        assert data["description"] == "Moderator role"

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(
        self, client: AsyncClient, admin_token: str, test_role
    ):
        """Test role creation fails with duplicate name."""
        role_data = {
            "name": test_role.name,
            "description": "Duplicate role",
        }

        response = await client.post(
            "/api/roles/",
            json=role_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_role_unauthorized(self, client: AsyncClient):
        """Test role creation fails without auth token."""
        role_data = {
            "name": "moderator",
            "description": "Moderator role",
        }

        response = await client.post(
            "/api/roles/",
            json=role_data,
        )

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_role_by_id(self, client: AsyncClient, test_role):
        """Test get role by ID."""
        response = await client.get(f"/api/roles/id/{test_role.id}/")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_role.id
        assert data["name"] == test_role.name
        assert data["description"] == test_role.description

    @pytest.mark.asyncio
    async def test_get_role_not_found(self, client: AsyncClient):
        """Test get role by ID returns 404 for non-existent role."""
        response = await client.get("/api/roles/id/99999/")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_role_success(self, client: AsyncClient, admin_token: str, test_role):
        """Test successful role update."""
        update_data = {"description": "Updated description"}

        response = await client.put(
            f"/api/roles/{test_role.id}/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_role.id
        assert data["name"] == test_role.name
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, client: AsyncClient, admin_token: str):
        """Test update role returns 404 for non-existent role."""
        update_data = {"description": "Updated description"}

        response = await client.put(
            "/api/roles/99999/",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_role_success(
        self, client: AsyncClient, admin_token: str, test_role: RoleDB
    ):
        """Test successful role deletion."""
        response = await client.delete(
            f"/api/roles/{test_role.id}/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_role_with_users_fails(
        self, client: AsyncClient, admin_token: str, test_role: RoleDB, test_db: Database
    ):
        """Test delete role fails when role is assigned to users."""
        from sqlalchemy import select

        from src.auth.security import get_password_hash

        async with test_db.async_session() as db_session:
            # Refresh role from current session to avoid session attachment issues
            stmt = select(RoleDB).where(RoleDB.id == test_role.id)
            result = await db_session.execute(stmt)
            role = result.scalar_one()

            user_data = UserSchemaCreate(
                username="test_user_with_role",
                email="userwithrole@example.com",
                password="SecurePass123!",
            )
            user_obj = UserDB(
                username=user_data.username,
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
            )
            user_obj.roles = [role]
            db_session.add(user_obj)
            await db_session.flush()

        response = await client.delete(
            f"/api/roles/{test_role.id}/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "assigned" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_search_roles_paginated(self, client: AsyncClient, test_role):
        """Test search roles with pagination."""
        response = await client.get(
            "/api/roles/paginated",
            params={
                "page": 1,
                "items_per_page": 10,
                "order_by": "name",
                "ascending": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert isinstance(data["data"], list)
        assert data["metadata"]["page"] == 1

    @pytest.mark.asyncio
    async def test_search_roles_with_query(self, client: AsyncClient, test_role):
        """Test search roles with name query."""
        response = await client.get(
            "/api/roles/paginated",
            params={
                "page": 1,
                "items_per_page": 10,
                "search": "test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0
        assert any(role["name"] == "test_role" for role in data["data"])
