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

    async def test_search_users_by_email(self, test_db):
        """Test search by email."""
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
        assert result.metadata.total_items == 1
        assert len(result.data) == 1
        assert result.data[0].username == "email_user"
        assert result.data[0].email == "searchable@example.com"

    async def test_search_users_by_first_name(self, test_db):
        """Test search by first name."""
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
        assert result.metadata.total_items == 1
        assert len(result.data) == 1

    async def test_search_users_by_second_name(self, test_db):
        """Test search by second name."""
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
        assert result.metadata.total_items == 1
        assert len(result.data) == 1

    async def test_search_users_cyrillic_characters(self, test_db):
        """Test search with cyrillic characters using ICU collation."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2005, first_name="Алексей", second_name="Петров")
            session.add(person)
            await session.flush()
            await session.refresh(person)

        from src.core.models.user import UserDB

        async with test_db.async_session() as session:
            user = UserDB(
                username="alexey_user",
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
        """Test search matches partial substrings."""
        from src.core.models import PersonDB

        service = UserServiceDB(test_db)

        async with test_db.async_session() as session:
            person = PersonDB(person_eesl_id=2010, first_name="PartialMatch", second_name="Test")
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
