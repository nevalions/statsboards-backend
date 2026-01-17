"""Test role service layer."""

import pytest
from fastapi import HTTPException

from src.auth.security import get_password_hash
from src.core.models import RoleDB, UserDB, UserRoleDB
from src.core.models.base import Database
from src.roles.db_services import RoleServiceDB
from src.roles.schemas import RoleSchemaCreate, RoleSchemaUpdate


@pytest.fixture
async def role_service(test_db: Database):
    """Get role service instance."""
    return RoleServiceDB(test_db)


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


class TestRoleService:
    """Test role service methods."""

    @pytest.mark.asyncio
    async def test_create_role(self, role_service: RoleServiceDB):
        """Test role creation."""
        role_data = RoleSchemaCreate(
            name="new_role",
            description="New role description",
        )

        role = await role_service.create(role_data)

        assert role.id is not None
        assert role.name == "new_role"
        assert role.description == "New role description"

    @pytest.mark.asyncio
    async def test_create_duplicate_role_fails(self, role_service: RoleServiceDB):
        """Test creating duplicate role fails."""
        role_data = RoleSchemaCreate(
            name="duplicate_role",
            description="Duplicate description",
        )

        await role_service.create(role_data)

        duplicate_data = RoleSchemaCreate(
            name="duplicate_role",
            description="Another description",
        )

        with pytest.raises(HTTPException):
            await role_service.create(duplicate_data)

    @pytest.mark.asyncio
    async def test_get_by_id_with_user_count(self, role_service: RoleServiceDB, test_role: RoleDB):
        """Test get role by ID with user count."""
        role = await role_service.get_by_id_with_user_count(test_role.id)

        assert role is not None
        assert role.id == test_role.id
        assert role.name == test_role.name
        assert role.user_count == 0

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, role_service: RoleServiceDB):
        """Test get role by ID returns None for non-existent role."""
        role = await role_service.get_by_id_with_user_count(99999)

        assert role is None

    @pytest.mark.asyncio
    async def test_update_role(self, role_service: RoleServiceDB, test_role):
        """Test role update."""
        update_data = RoleSchemaUpdate(description="Updated description")

        role = await role_service.update(test_role.id, update_data)

        assert role.id == test_role.id
        assert role.name == test_role.name
        assert role.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, role_service: RoleServiceDB):
        """Test update role returns None for non-existent role."""
        update_data = RoleSchemaUpdate(description="Updated description")

        with pytest.raises(HTTPException):
            await role_service.update(99999, update_data)

    @pytest.mark.asyncio
    async def test_delete_role(self, role_service: RoleServiceDB, test_role):
        """Test role deletion."""
        await role_service.delete(test_role.id)

        role = await role_service.get_by_id_with_user_count(test_role.id)
        assert role is None

    @pytest.mark.asyncio
    async def test_delete_role_with_users_fails(
        self, role_service: RoleServiceDB, test_db: Database
    ):
        """Test delete role fails when role is assigned to users."""
        role_data = RoleSchemaCreate(name="test_role_with_users", description="Role for testing")
        role = await role_service.create(role_data)

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": get_password_hash("password123"),
        }

        async with test_db.async_session() as db_session:
            user_obj = UserDB(**user_data)
            db_session.add(user_obj)
            await db_session.flush()
            user_id = user_obj.id

            user_role = UserRoleDB(user_id=user_id, role_id=role.id)
            db_session.add(user_role)
            await db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            await role_service.delete(role.id)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_search_roles_with_pagination(self, role_service: RoleServiceDB, test_role):
        """Test search roles with pagination."""
        response = await role_service.search_roles_with_pagination(
            search_query="test",
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        assert response is not None
        assert len(response.data) > 0
        assert any(role.name == "test_role" for role in response.data)
        assert response.metadata.page == 1
