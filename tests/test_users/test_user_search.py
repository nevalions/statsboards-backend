"""Test user search functionality."""

import pytest

from src.users.db_services import UserServiceDB
from src.users.schemas import PaginatedUserResponse


@pytest.mark.asyncio
class TestUserSearch:
    """Test user search with pagination."""

    async def test_search_users_empty_query(self, test_db):
        """Test search with empty query returns all users."""
        from src.core.models import PersonDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person1 = PersonDB(person_eesl_id=1001, first_name="John", second_name="Doe")
            person2 = PersonDB(person_eesl_id=1002, first_name="Jane", second_name="Smith")
            person3 = PersonDB(person_eesl_id=1003, first_name="Иван", second_name="Иванов")

            session.add_all([person1, person2, person3])
            await session.flush()
            await session.refresh(person1)
            await session.refresh(person2)
            await session.refresh(person3)

            user1 = UserDB(
                username="john_doe",
                email="john@example.com",
                hashed_password="hashed_password",
                person_id=person1.id,
                is_active=True,
            )
            user2 = UserDB(
                username="jane_smith",
                email="jane@example.com",
                hashed_password="hashed_password",
                person_id=person2.id,
                is_active=True,
            )
            user3 = UserDB(
                username="ivan_ivanov",
                email="ivan@example.com",
                hashed_password="hashed_password",
                person_id=person3.id,
                is_active=False,
            )
            session.add_all([user1, user2, user3])
            await session.flush()
            await session.refresh(user1)
            await session.refresh(user2)
            await session.refresh(user3)

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 3
        assert len(result.data) == 3
        assert result.metadata.page == 1

    async def test_search_users_by_username(self, test_db):
        """Test search by username."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2001, first_name="John", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="searchable_user",
                email="searchable1@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            user2 = UserDB(
                username="other_user",
                email="other@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add_all([user1, user2])
            await session.flush()
            await session.refresh(user1)
            await session.refresh(user2)

        result = await service.search_users_with_pagination(
            search_query="searchable",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1
        assert result.data[0].username == "searchable_user"

    async def test_search_users_by_email_returns_empty(self, test_db):
        """Test search by email returns no results (search is username-only)."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2002, first_name="John", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="email_user",
                email="searchable@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            user2 = UserDB(
                username="other_user",
                email="other@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add_all([user1, user2])
            await session.flush()
            await session.refresh(user1)
            await session.refresh(user2)

        result = await service.search_users_with_pagination(
            search_query="searchable",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 0
        assert len(result.data) == 0

    async def test_search_users_by_first_name_returns_empty(self, test_db):
        """Test search by first name returns no results (search is username-only)."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2003, first_name="TestName", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="nameuser",
                email="name@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

        result = await service.search_users_with_pagination(
            search_query="TestName",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 0
        assert len(result.data) == 0

    async def test_search_users_by_second_name_returns_empty(self, test_db):
        """Test search by second name returns no results (search is username-only)."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2004, first_name="John", second_name="Searchable")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="surnameuser",
                email="surname@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

        result = await service.search_users_with_pagination(
            search_query="Searchable",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 0
        assert len(result.data) == 0

    async def test_search_users_cyrillic_characters_in_username(self, test_db):
        """Test search with cyrillic characters using ICU collation."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2005, first_name="John", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="Алексей",
                email="alexey@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

        result = await service.search_users_with_pagination(
            search_query="Алексей",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1

    async def test_search_users_case_insensitive(self, test_db):
        """Test search is case-insensitive."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2006, first_name="John", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="CaseUser",
                email="case@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

        result = await service.search_users_with_pagination(
            search_query="caseuser",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1

    async def test_search_users_pagination(self, test_db):
        """Test pagination works correctly."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2007, first_name="Pagination", second_name="Test")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            for i in range(5):
                user = UserDB(
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    hashed_password="hashed_password",
                    person_id=person.id,
                    is_active=True,
                )
                session.add(user)
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=2,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 5
        assert len(result.data) == 2
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 2
        assert result.metadata.total_pages == 3
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is False

        result_page_2 = await service.search_users_with_pagination(
            search_query=None,
            skip=2,
            limit=2,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert result_page_2.metadata.page == 2
        assert result_page_2.metadata.has_next is True
        assert result_page_2.metadata.has_previous is True

        result_page_3 = await service.search_users_with_pagination(
            search_query=None,
            skip=4,
            limit=2,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert result_page_3.metadata.page == 3
        assert result_page_3.metadata.has_next is False
        assert result_page_3.metadata.has_previous is True

    async def test_search_users_no_results(self, test_db):
        """Test search with no matching results."""
        service = UserServiceDB(test_db)

        result = await service.search_users_with_pagination(
            search_query="nonexistent",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 0
        assert len(result.data) == 0
        assert result.metadata.total_pages == 0

    async def test_search_users_ordering(self, test_db):
        """Test ordering by username and id."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2008, first_name="Order", second_name="Test")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="b_user",
                email="b@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            user2 = UserDB(
                username="a_user",
                email="a@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            user3 = UserDB(
                username="c_user",
                email="c@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add_all([user1, user2, user3])
            await session.flush()
            await session.refresh(user1)
            await session.refresh(user2)
            await session.refresh(user3)

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert len(result.data) == 3
        usernames = [user.username for user in result.data]
        assert usernames == ["a_user", "b_user", "c_user"]

        result_desc = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=False,
        )

        usernames_desc = [user.username for user in result_desc.data]
        assert usernames_desc == ["c_user", "b_user", "a_user"]

    async def test_search_users_metadata(self, test_db):
        """Test pagination metadata structure."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2009, first_name="Metadata", second_name="Test")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            for i in range(3):
                user = UserDB(
                    username=f"user{i}",
                    email=f"user{i}@example.com",
                    hashed_password="hashed_password",
                    person_id=person.id,
                    is_active=True,
                )
                session.add(user)
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert result.metadata.total_items == 3
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 20
        assert result.metadata.total_pages == 1
        assert result.metadata.has_next is False
        assert result.metadata.has_previous is False

    async def test_search_users_partial_substring_match(self, test_db):
        """Test search matches partial substrings in username."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2010, first_name="John", second_name="Doe")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="partialuser",
                email="partial@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)

        result = await service.search_users_with_pagination(
            search_query="Part",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
        )

        assert result.metadata.total_items == 1
        assert result.data[0].username == "partialuser"

    async def test_search_users_by_role_single(self, test_db):
        """Test search filters by a single role."""
        from src.core.models import PersonDB, RoleDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=3001, first_name="Test", second_name="User")
            admin_role = RoleDB(name="admin", description="Admin role")
            user_role = RoleDB(name="user", description="User role")
            session.add_all([person, admin_role, user_role])
            await session.flush()
            await session.refresh(person)
            await session.refresh(admin_role)
            await session.refresh(user_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[admin_role],
            )
            regular_user = UserDB(
                username="regular_user",
                email="regular@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[user_role],
            )
            session.add_all([admin_user, regular_user])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            role_names=["admin"],
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1
        assert result.data[0].username == "admin_user"
        assert "admin" in result.data[0].roles

    async def test_search_users_by_role_multiple(self, test_db):
        """Test search filters by multiple roles (OR logic)."""
        from src.core.models import PersonDB, RoleDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=3002, first_name="Test", second_name="User")
            admin_role = RoleDB(name="admin", description="Admin role")
            moderator_role = RoleDB(name="moderator", description="Moderator role")
            user_role = RoleDB(name="user", description="User role")
            session.add_all([person, admin_role, moderator_role, user_role])
            await session.flush()
            await session.refresh(person)
            await session.refresh(admin_role)
            await session.refresh(moderator_role)
            await session.refresh(user_role)

            admin_user = UserDB(
                username="admin_user",
                email="admin@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[admin_role],
            )
            moderator_user = UserDB(
                username="mod_user",
                email="mod@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[moderator_role],
            )
            regular_user = UserDB(
                username="regular_user",
                email="regular@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[user_role],
            )
            session.add_all([admin_user, moderator_user, regular_user])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            role_names=["admin", "moderator"],
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 2
        usernames = {user.username for user in result.data}
        assert usernames == {"admin_user", "mod_user"}

    async def test_search_users_by_role_with_search(self, test_db):
        """Test search filters by role combined with username search."""
        from src.core.models import PersonDB, RoleDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person1 = PersonDB(person_eesl_id=3003, first_name="John", second_name="Admin")
            person2 = PersonDB(person_eesl_id=3004, first_name="Jane", second_name="User")
            admin_role = RoleDB(name="admin", description="Admin role")
            user_role = RoleDB(name="user", description="User role")
            session.add_all([person1, person2, admin_role, user_role])
            await session.flush()
            await session.refresh(person1)
            await session.refresh(person2)
            await session.refresh(admin_role)
            await session.refresh(user_role)

            admin_user = UserDB(
                username="john_admin",
                email="john@example.com",
                hashed_password="hashed_password",
                person_id=person1.id,
                is_active=True,
                roles=[admin_role],
            )
            regular_user = UserDB(
                username="jane_user",
                email="jane@example.com",
                hashed_password="hashed_password",
                person_id=person2.id,
                is_active=True,
                roles=[user_role],
            )
            session.add_all([admin_user, regular_user])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query="john",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            role_names=["admin"],
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert result.data[0].username == "john_admin"

    async def test_search_users_by_nonexistent_role(self, test_db):
        """Test search with nonexistent role returns empty results."""
        from src.core.models import PersonDB, RoleDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=3005, first_name="Test", second_name="User")
            user_role = RoleDB(name="user", description="User role")
            session.add_all([person, user_role])
            await session.flush()
            await session.refresh(person)
            await session.refresh(user_role)

            user = UserDB(
                username="test_user",
                email="test@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                roles=[user_role],
            )
            session.add(user)
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            role_names=["nonexistent_role"],
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 0
        assert len(result.data) == 0

    async def test_search_users_sort_by_is_online(self, test_db):
        """Test sorting by is_online field."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4001, first_name="Test", second_name="User")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="online_user",
                email="online@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            user2 = UserDB(
                username="offline_user",
                email="offline@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            session.add_all([user1, user2])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="is_online",
            order_by_two="username",
            ascending=False,
        )

        assert len(result.data) == 2
        assert result.data[0].is_online is True
        assert result.data[0].username == "online_user"
        assert result.data[1].is_online is False
        assert result.data[1].username == "offline_user"

    async def test_search_users_filter_by_online_true(self, test_db):
        """Test search filters users by is_online=true."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4002, first_name="Test", second_name="User")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="online_user1",
                email="online1@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            user2 = UserDB(
                username="offline_user1",
                email="offline1@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            user3 = UserDB(
                username="online_user2",
                email="online2@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            session.add_all([user1, user2, user3])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            is_online=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 2
        assert len(result.data) == 2
        usernames = {user.username for user in result.data}
        assert usernames == {"online_user1", "online_user2"}
        assert all(user.is_online for user in result.data)

    async def test_search_users_filter_by_online_false(self, test_db):
        """Test search filters users by is_online=false."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4003, first_name="Test", second_name="User")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="online_user",
                email="online@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            user2 = UserDB(
                username="offline_user1",
                email="offline1@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            user3 = UserDB(
                username="offline_user2",
                email="offline2@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            session.add_all([user1, user2, user3])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            is_online=False,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 2
        assert len(result.data) == 2
        usernames = {user.username for user in result.data}
        assert usernames == {"offline_user1", "offline_user2"}
        assert all(not user.is_online for user in result.data)

    async def test_search_users_filter_by_online_none(self, test_db):
        """Test search with is_online=None returns all users."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4004, first_name="Test", second_name="User")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="online_user",
                email="online@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            user2 = UserDB(
                username="offline_user",
                email="offline@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            session.add_all([user1, user2])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            is_online=None,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 2
        assert len(result.data) == 2

    async def test_search_users_filter_by_online_with_role(self, test_db):
        """Test search filters by is_online combined with role filter."""
        from src.core.models import PersonDB, RoleDB, UserDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4005, first_name="Test", second_name="User")
            admin_role = RoleDB(name="admin", description="Admin role")
            user_role = RoleDB(name="user", description="User role")
            session.add_all([person, admin_role, user_role])
            await session.flush()
            await session.refresh(person)
            await session.refresh(admin_role)
            await session.refresh(user_role)

            online_admin = UserDB(
                username="online_admin",
                email="online_admin@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
                roles=[admin_role],
            )
            offline_admin = UserDB(
                username="offline_admin",
                email="offline_admin@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
                roles=[admin_role],
            )
            online_user = UserDB(
                username="online_user",
                email="online_user@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
                roles=[user_role],
            )
            session.add_all([online_admin, offline_admin, online_user])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query=None,
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            role_names=["admin"],
            is_online=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1
        assert result.data[0].username == "online_admin"
        assert result.data[0].is_online is True
        assert "admin" in result.data[0].roles

    async def test_search_users_filter_by_online_with_search(self, test_db):
        """Test search filters by is_online combined with username search."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=4006, first_name="Test", second_name="User")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user1 = UserDB(
                username="test_online",
                email="test_online@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            user2 = UserDB(
                username="test_offline",
                email="test_offline@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=False,
            )
            user3 = UserDB(
                username="other_online",
                email="other_online@example.com",
                hashed_password="hashed_password",
                person_id=person.id,
                is_active=True,
                is_online=True,
            )
            session.add_all([user1, user2, user3])
            await session.flush()

        result = await service.search_users_with_pagination(
            search_query="test",
            skip=0,
            limit=20,
            order_by="username",
            order_by_two="id",
            ascending=True,
            is_online=True,
        )

        assert isinstance(result, PaginatedUserResponse)
        assert result.metadata.total_items == 1
        assert len(result.data) == 1
        assert result.data[0].username == "test_online"
        assert result.data[0].is_online is True
