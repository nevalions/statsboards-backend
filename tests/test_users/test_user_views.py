"""Test user views/endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.auth.security import create_access_token, get_password_hash, verify_password
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
        user_obj = UserDB(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
        )
        db_session.add(user_obj)
        await db_session.flush()
        await db_session.refresh(user_obj)

        yield user_obj

        await db_session.delete(user_obj)


class TestUserViews:
    """Test user API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
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
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration fails with duplicate username."""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "SecurePass123!",
        }

        response = await client.post("/api/users/register", json=user_data)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient, test_user):
        """Test /users/me endpoint with valid token."""

        token = create_access_token(data={"sub": str(test_user.id)})

        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test /users/me endpoint without token returns 401."""
        response = await client.get("/api/users/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_me_authenticated(self, client: AsyncClient, test_user):
        """Test updating current user profile."""

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
    async def test_update_me_unauthorized(self, client: AsyncClient):
        """Test updating profile without token returns 401."""
        update_data = {"email": "updated@example.com"}
        response = await client.put("/api/users/me", json=update_data)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_db: Database):
        """Test registration fails with duplicate email."""
        async with test_db.async_session() as db_session:
            user_data = UserSchemaCreate(
                username="existing_user",
                email="existing@example.com",
                password="SecurePass123!",
            )
            user = UserDB(
                username=user_data.username,
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
            )
            db_session.add(user)
            await db_session.flush()

        response = await client.post(
            "/api/users/register",
            json={
                "username": "new_user",
                "email": "existing@example.com",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_user_roles(self, client: AsyncClient, test_db: Database, test_user):
        """Test getting user roles (admin only)."""
        from sqlalchemy.orm import selectinload

        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

            user_role = RoleDB(name="custom_role", description="Custom role")
            db_session.add(user_role)
            await db_session.flush()
            await db_session.refresh(user_role)

            stmt = (
                select(UserDB).where(UserDB.id == test_user.id).options(selectinload(UserDB.roles))
            )
            result = await db_session.execute(stmt)
            test_user_with_roles = result.scalar_one_or_none()
            test_user_with_roles.roles.append(user_role)
            await db_session.flush()

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        response = await client.get(
            f"/api/users/{test_user.id}/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "custom_role" in data["roles"]

    @pytest.mark.asyncio
    async def test_get_user_roles_not_admin(self, client: AsyncClient, test_user):
        """Test getting user roles without admin role returns 403."""
        token = create_access_token(data={"sub": str(test_user.id)})

        response = await client.get(
            f"/api/users/{test_user.id}/roles",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_roles_unauthorized(self, client: AsyncClient, test_user):
        """Test getting user roles without token returns 401."""
        response = await client.get(f"/api/users/{test_user.id}/roles")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_roles_not_found(self, client: AsyncClient, test_db: Database):
        """Test getting roles for non-existent user returns 404."""
        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        response = await client.get(
            "/api/users/99999/roles",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, test_db: Database, test_user):
        """Test getting user by ID with roles (admin only)."""
        from sqlalchemy.orm import selectinload

        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

            user_role = RoleDB(name="custom_role", description="Custom role")
            db_session.add(user_role)
            await db_session.flush()
            await db_session.refresh(user_role)

            stmt = (
                select(UserDB).where(UserDB.id == test_user.id).options(selectinload(UserDB.roles))
            )
            result = await db_session.execute(stmt)
            test_user_with_roles = result.scalar_one_or_none()
            test_user_with_roles.roles.append(user_role)
            await db_session.flush()

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        response = await client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert "custom_role" in data["roles"]

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_admin(self, client: AsyncClient, test_user):
        """Test getting user by ID without admin role returns 403."""
        token = create_access_token(data={"sub": str(test_user.id)})

        response = await client.get(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_user_by_id_unauthorized(self, client: AsyncClient, test_user):
        """Test getting user by ID without token returns 401."""
        response = await client.get(f"/api/users/{test_user.id}")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, client: AsyncClient, test_db: Database):
        """Test getting non-existent user returns 404."""
        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        response = await client.get(
            "/api/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_by_id(self, client: AsyncClient, test_db: Database, test_user):
        """Test updating user by ID (admin only)."""
        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        update_data = {"email": "updated_admin@example.com", "is_active": False}
        response = await client.put(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated_admin@example.com"
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_update_user_by_id_not_admin(self, client: AsyncClient, test_user):
        """Test updating user by ID without admin role returns 403."""
        token = create_access_token(data={"sub": str(test_user.id)})

        update_data = {"email": "updated@example.com"}
        response = await client.put(
            f"/api/users/{test_user.id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_change_password(self, client: AsyncClient, test_db: Database, test_user):
        """Test admin changing user password."""
        from src.auth.security import verify_password
        from src.core.models import RoleDB

        async with test_db.async_session() as db_session:
            admin_role = RoleDB(name="admin", description="Administrator role")
            db_session.add(admin_role)
            await db_session.flush()
            await db_session.refresh(admin_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password=get_password_hash("AdminPass123!"),
            )
            admin_user.roles = [admin_role]
            db_session.add(admin_user)
            await db_session.flush()
            await db_session.refresh(admin_user)

        admin_token = create_access_token(data={"sub": str(admin_user.id)})

        password_data = {"new_password": "NewAdminPassword123!"}
        response = await client.post(
            f"/api/users/{test_user.id}/change-password",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=password_data,
        )

        assert response.status_code == 200

        async with test_db.async_session() as db_session:
            stmt = select(UserDB).where(UserDB.id == test_user.id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            assert verify_password("NewAdminPassword123!", user.hashed_password)

    @pytest.mark.asyncio
    async def test_admin_change_password_not_admin(self, client: AsyncClient, test_user):
        """Test admin changing password without admin role returns 403."""
        token = create_access_token(data={"sub": str(test_user.id)})

        password_data = {"new_password": "NewPassword123!"}
        response = await client.post(
            f"/api/users/{test_user.id}/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json=password_data,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_change_own_password_success(
        self, client: AsyncClient, test_db: Database, test_user
    ):
        """Test changing own password with correct current password."""

        async with test_db.async_session() as db_session:
            stmt = select(UserDB).where(UserDB.id == test_user.id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            original_hash = user.hashed_password

        token = create_access_token(data={"sub": str(test_user.id)})
        password_data = {"old_password": "SecurePass123!", "new_password": "NewPassword123!"}
        response = await client.post(
            "/api/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json=password_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"

        async with test_db.async_session() as db_session:
            stmt = select(UserDB).where(UserDB.id == test_user.id)
            result = await db_session.execute(stmt)
            user = result.scalar_one_or_none()
            assert user.hashed_password != original_hash
            assert verify_password("NewPassword123!", user.hashed_password)

    @pytest.mark.asyncio
    async def test_change_own_password_wrong_current_password(self, client: AsyncClient, test_user):
        """Test changing own password with wrong current password returns 400."""
        token = create_access_token(data={"sub": str(test_user.id)})
        password_data = {"old_password": "WrongPassword123!", "new_password": "NewPassword123!"}
        response = await client.post(
            "/api/users/me/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json=password_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "Incorrect password" in data["detail"]

    @pytest.mark.asyncio
    async def test_change_own_password_unauthorized(self, client: AsyncClient, test_user):
        """Test changing own password without token returns 401."""
        password_data = {"old_password": "SecurePass123!", "new_password": "NewPassword123!"}
        response = await client.post(
            "/api/users/me/change-password",
            json=password_data,
        )

        assert response.status_code == 401
