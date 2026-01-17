"""Test role search functionality."""

import pytest

from src.core.models import RoleDB
from src.core.models.base import Database
from src.roles.db_services import RoleServiceDB


@pytest.fixture
async def role_service(test_db: Database):
    """Get role service instance."""
    return RoleServiceDB(test_db)


@pytest.fixture
async def sample_roles(test_db: Database):
    """Create sample roles for search testing."""
    async with test_db.async_session() as db_session:
        roles = []
        role_names = ["admin", "moderator", "user", "guest", "editor"]

        for name in role_names:
            role = RoleDB(name=name, description=f"{name} role")
            db_session.add(role)
            await db_session.flush()
            await db_session.refresh(role)
            roles.append(role)

        yield roles

        for role in roles:
            await db_session.delete(role)


class TestRoleSearch:
    """Test role search with pagination."""

    @pytest.mark.asyncio
    async def test_search_roles_no_filter(self, role_service: RoleServiceDB, sample_roles):
        """Test search returns all roles when no filter is applied."""
        response = await role_service.search_roles_with_pagination(
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        assert len(response.data) == len(sample_roles)
        assert response.metadata.total_items == len(sample_roles)

    @pytest.mark.asyncio
    async def test_search_roles_by_name(self, role_service: RoleServiceDB, sample_roles):
        """Test search roles by name pattern."""
        response = await role_service.search_roles_with_pagination(
            search_query="ad",
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        assert len(response.data) == 1
        assert response.data[0].name == "admin"

    @pytest.mark.asyncio
    async def test_search_roles_pagination(self, role_service: RoleServiceDB, sample_roles):
        """Test pagination works correctly."""
        response_page1 = await role_service.search_roles_with_pagination(
            skip=0,
            limit=2,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        response_page2 = await role_service.search_roles_with_pagination(
            skip=2,
            limit=2,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        assert len(response_page1.data) == 2
        assert len(response_page2.data) == 2
        assert response_page1.metadata.page == 1
        assert response_page2.metadata.page == 2

    @pytest.mark.asyncio
    async def test_search_roles_ordering_ascending(self, role_service: RoleServiceDB, sample_roles):
        """Test ascending order by name."""
        response = await role_service.search_roles_with_pagination(
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        role_names = [role.name for role in response.data]
        assert role_names == sorted(role_names)

    @pytest.mark.asyncio
    async def test_search_roles_ordering_descending(
        self, role_service: RoleServiceDB, sample_roles
    ):
        """Test descending order by name."""
        response = await role_service.search_roles_with_pagination(
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=False,
        )

        role_names = [role.name for role in response.data]
        assert role_names == sorted(role_names, reverse=True)

    @pytest.mark.asyncio
    async def test_search_roles_empty_result(self, role_service: RoleServiceDB):
        """Test search returns empty result when no roles match."""
        response = await role_service.search_roles_with_pagination(
            search_query="nonexistent",
            skip=0,
            limit=10,
            order_by="name",
            order_by_two="id",
            ascending=True,
        )

        assert len(response.data) == 0
        assert response.metadata.total_items == 0
