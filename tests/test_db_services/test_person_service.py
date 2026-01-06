import pytest

from src.core.models import PersonDB
from src.core.models.base import Database
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaUpdate
from tests.factories import PersonFactory


@pytest.mark.asyncio
class TestPersonServiceDBCreateOrUpdate:
    """Test create_or_update_person functionality."""

    async def test_create_person_with_eesl_id(self, test_db: Database):
        """Test creating a person with eesl_id."""
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build(person_eesl_id=100, first_name="John", second_name="Doe")

        result = await person_service.create_or_update_person(person_data)

        assert result is not None
        assert result.id is not None
        assert result.person_eesl_id == 100
        assert result.first_name == "John"
        assert result.second_name == "Doe"

    async def test_create_person_without_eesl_id(self, test_db: Database):
        """Test creating a person without eesl_id."""
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build(
            person_eesl_id=None, first_name="Jane", second_name="Smith"
        )

        result = await person_service.create_or_update_person(person_data)

        assert result is not None
        assert result.id is not None
        assert result.person_eesl_id is None
        assert result.first_name == "Jane"

    async def test_update_existing_person_by_eesl_id(self, test_db: Database):
        """Test updating an existing person by eesl_id."""
        person_service = PersonServiceDB(test_db)

        person_data = PersonFactory.build(
            person_eesl_id=200, first_name="Original", second_name="Name"
        )
        created = await person_service.create_or_update_person(person_data)

        update_data = PersonSchemaUpdate(
            person_eesl_id=200, first_name="Updated", second_name="Name"
        )

        updated = await person_service.create_or_update_person(update_data)

        assert updated.id == created.id
        assert updated.first_name == "Updated"
        assert updated.second_name == "Name"

    async def test_create_multiple_persons(self, test_db: Database):
        """Test creating multiple persons."""
        person_service = PersonServiceDB(test_db)

        person1_data = PersonFactory.build(person_eesl_id=301, first_name="Person 1")
        person2_data = PersonFactory.build(person_eesl_id=302, first_name="Person 2")
        person3_data = PersonFactory.build(person_eesl_id=303, first_name="Person 3")

        person1 = await person_service.create_or_update_person(person1_data)
        person2 = await person_service.create_or_update_person(person2_data)
        person3 = await person_service.create_or_update_person(person3_data)

        assert person1.person_eesl_id == 301
        assert person2.person_eesl_id == 302
        assert person3.person_eesl_id == 303
        assert person1.id != person2.id != person3.id

    async def test_update_person_partial_fields(self, test_db: Database):
        """Test updating only some person fields."""
        person_service = PersonServiceDB(test_db)

        person_data = PersonFactory.build(
            person_eesl_id=400,
            first_name="Full Name",
            person_photo_url="http://old.url",
        )
        created = await person_service.create_or_update_person(person_data)

        update_data = PersonSchemaUpdate(person_eesl_id=400, person_photo_url="http://new.url")

        updated = await person_service.create_or_update_person(update_data)

        assert updated.id == created.id
        assert updated.first_name == "Full Name"
        assert updated.person_photo_url == "http://new.url"

    async def test_upsert_create_then_update(self, test_db: Database):
        """Test creating then updating same person in sequence."""
        person_service = PersonServiceDB(test_db)

        create_data = PersonFactory.build(
            person_eesl_id=500, first_name="Create", second_name="Test"
        )
        created = await person_service.create_or_update_person(create_data)

        update_data = PersonSchemaUpdate(person_eesl_id=500, second_name="Updated")
        updated = await person_service.create_or_update_person(update_data)

        assert created.id == updated.id
        assert created.second_name == "Test"
        assert updated.second_name == "Updated"

    async def test_get_person_by_eesl_id(self, test_db: Database):
        """Test retrieving person by eesl_id."""
        person_service = PersonServiceDB(test_db)

        person_data = PersonFactory.build(person_eesl_id=600, first_name="Get")
        created = await person_service.create_or_update_person(person_data)

        retrieved = await person_service.get_person_by_eesl_id(600)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.first_name == "Get"


@pytest.mark.asyncio
class TestPersonServiceDBPagination:
    """Test pagination functionality."""

    async def test_get_all_persons_with_pagination_success(self, test_db: Database):
        """Test paginated retrieval returns correct number of items."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1001, first_name="Alice", second_name="Zoe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1002, first_name="Bob", second_name="Smith")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=1003, first_name="Charlie", second_name="Brown")
        )

        persons = await person_service.get_all_persons_with_pagination(
            skip=0, limit=2, order_by="second_name"
        )

        assert len(persons) == 2
        assert all(isinstance(p, PersonDB) for p in persons)
        second_names = [p.second_name for p in persons]
        assert second_names == ["Brown", "Smith"]

    async def test_get_all_persons_with_pagination_ordering(self, test_db: Database):
        """Test pagination ordering by second_name."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2001, first_name="Alice", second_name="Zoe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2002, first_name="Bob", second_name="Alpha")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2003, first_name="Charlie", second_name="Middle")
        )

        persons = await person_service.get_all_persons_with_pagination(
            skip=0, limit=10, order_by="second_name", ascending=True
        )
        second_names = [p.second_name for p in persons]
        assert second_names == sorted(second_names)

        persons_desc = await person_service.get_all_persons_with_pagination(
            skip=0, limit=10, order_by="second_name", ascending=False
        )
        second_names_desc = [p.second_name for p in persons_desc]
        assert second_names_desc == sorted(second_names_desc, reverse=True)

    async def test_get_all_persons_with_pagination_empty_result(self, test_db: Database):
        """Test pagination with skip beyond available records."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3001, first_name="Test")
        )

        persons = await person_service.get_all_persons_with_pagination(skip=1000, limit=10)
        assert persons == []

    async def test_get_all_persons_with_pagination_default_sort(self, test_db: Database):
        """Test pagination uses default sort by second_name."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=4001, first_name="A", second_name="Zebra")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=4002, first_name="B", second_name="Apple")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=4003, first_name="C", second_name="Mango")
        )

        persons = await person_service.get_all_persons_with_pagination(skip=0, limit=10)
        second_names = [p.second_name for p in persons]
        assert second_names == ["Apple", "Mango", "Zebra"]

    async def test_get_persons_count(self, test_db: Database):
        """Test count returns correct number of records."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=5001, first_name="One")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=5002, first_name="Two")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=5003, first_name="Three")
        )

        count = await person_service.get_persons_count()
        assert count == 3

    async def test_get_persons_count_empty(self, test_db: Database):
        """Test count returns zero when no records."""
        person_service = PersonServiceDB(test_db)

        count = await person_service.get_persons_count()
        assert count == 0


@pytest.mark.asyncio
class TestPersonServiceDBSearch:
    """Test full-text search functionality."""

    async def test_search_persons_with_pagination_success(self, test_db: Database):
        """Test search returns correct results."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2001, first_name="Alice", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2002, first_name="Bob", second_name="Smith")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=2003, first_name="Charlie", second_name="Johnson")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="Johnson", skip=0, limit=10, order_by="second_name"
        )

        assert result is not None
        assert len(result.data) == 2
        names = [p.first_name for p in result.data]
        assert "Alice" in names
        assert "Charlie" in names
        assert "Bob" not in names
        assert result.metadata.total_items == 2

    async def test_search_persons_with_pagination_empty_query(self, test_db: Database):
        """Test search with empty query returns all persons."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3001, first_name="Alice", second_name="Zoe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=3002, first_name="Bob", second_name="Alpha")
        )

        result = await person_service.search_persons_with_pagination(
            search_query=None, skip=0, limit=10
        )

        assert len(result.data) == 2
        assert result.metadata.total_items == 2

    async def test_search_persons_with_pagination_partial_match(self, test_db: Database):
        """Test search matches partial words (full-text search)."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(
                person_eesl_id=4001, first_name="Christopher", second_name="Anderson"
            )
        )

        result = await person_service.search_persons_with_pagination(
            search_query="Christopher", skip=0, limit=10
        )

        assert len(result.data) == 1
        assert result.data[0].first_name == "Christopher"

    async def test_search_persons_with_pagination_no_results(self, test_db: Database):
        """Test search with no matching results."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=5001, first_name="Alice", second_name="Smith")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="XYZNonExistent", skip=0, limit=10
        )

        assert len(result.data) == 0
        assert result.metadata.total_items == 0
        assert result.metadata.total_pages == 0

    async def test_search_persons_with_pagination_metadata(self, test_db: Database):
        """Test pagination metadata is calculated correctly."""
        person_service = PersonServiceDB(test_db)

        for i in range(5):
            await person_service.create_or_update_person(
                PersonFactory.build(
                    person_eesl_id=6000 + i,
                    first_name=f"Test{i}",
                    second_name="Smith",
                )
            )

        result = await person_service.search_persons_with_pagination(
            search_query="Smith", skip=0, limit=2, order_by="id"
        )

        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 2
        assert result.metadata.total_items == 5
        assert result.metadata.total_pages == 3
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is False

        result_page2 = await person_service.search_persons_with_pagination(
            search_query="Smith", skip=2, limit=2, order_by="id"
        )

        assert result_page2.metadata.page == 2
        assert result_page2.metadata.has_next is True
        assert result_page2.metadata.has_previous is True

        result_page3 = await person_service.search_persons_with_pagination(
            search_query="Smith", skip=4, limit=2, order_by="id"
        )

        assert result_page3.metadata.page == 3
        assert result_page3.metadata.has_next is False
        assert result_page3.metadata.has_previous is True

    async def test_search_persons_with_pagination_ordering(self, test_db: Database):
        """Test search with ordering."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=7001, first_name="Alice", second_name="Zebra")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=7002, first_name="Alice", second_name="Alpha")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="Alice", skip=0, limit=10, order_by="second_name", ascending=True
        )

        assert len(result.data) == 2
        assert result.data[0].second_name == "Alpha"
        assert result.data[1].second_name == "Zebra"

    async def test_search_persons_partial_substring_match(self, test_db: Database):
        """Test search matches partial substrings anywhere in first_name or second_name."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8001, first_name="Малахов", second_name="Alex")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8002, first_name="Паламарчук", second_name="Bob")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8003, first_name="Алабин", second_name="Charlie")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="ала", skip=0, limit=10
        )

        assert len(result.data) == 3
        names = [p.first_name for p in result.data]
        assert "Малахов" in names
        assert "Паламарчук" in names
        assert "Алабин" in names

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=8004, first_name="Christopher", second_name="Smith")
        )

        result_pher = await person_service.search_persons_with_pagination(
            search_query="pher", skip=0, limit=10
        )

        assert len(result_pher.data) == 1
        assert result_pher.data[0].first_name == "Christopher"

    async def test_search_persons_cyrillic_characters(self, test_db: Database):
        """Test search works with Cyrillic and multi-language characters."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=9001, first_name="Иванов", second_name="Ivan")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=9002, first_name="Пиванович", second_name="Piv")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=9003, first_name="Сииван", second_name="Sii")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=9004, first_name="иса абдулаев", second_name="Isa")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="иван", skip=0, limit=10
        )

        assert len(result.data) == 3
        names = [p.first_name for p in result.data]
        assert "Иванов" in names
        assert "Пиванович" in names
        assert "Сииван" in names

        result_isa = await person_service.search_persons_with_pagination(
            search_query="иса", skip=0, limit=10
        )

        assert len(result_isa.data) == 1
        assert result_isa.data[0].first_name == "иса абдулаев"

    async def test_search_persons_case_insensitive(self, test_db: Database):
        """Test search is case-insensitive (ILIKE)."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=10001, first_name="Alice", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=10002, first_name="Charlie", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=10003, first_name="Alice", second_name="Smith")
        )

        result_lower = await person_service.search_persons_with_pagination(
            search_query="johnson", skip=0, limit=10
        )

        assert len(result_lower.data) == 2
        names_lower = [p.first_name for p in result_lower.data]
        assert "Alice" in names_lower
        assert "Charlie" in names_lower

        result_mixed = await person_service.search_persons_with_pagination(
            search_query="aLiCe", skip=0, limit=10
        )

        assert len(result_mixed.data) == 2
        names_mixed = [p.first_name for p in result_mixed.data]
        assert "Alice" in names_mixed

        result_upper = await person_service.search_persons_with_pagination(
            search_query="JOHNSON", skip=0, limit=10
        )

        assert len(result_upper.data) == 2
        names_upper = [p.first_name for p in result_upper.data]
        assert "Alice" in names_upper
        assert "Charlie" in names_upper

    async def test_search_persons_first_or_second_name(self, test_db: Database):
        """Test search matches first_name OR second_name fields separately."""
        person_service = PersonServiceDB(test_db)

        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=11001, first_name="John", second_name="Doe")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=11002, first_name="Alice", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=11003, first_name="Charlie", second_name="Johnson")
        )
        await person_service.create_or_update_person(
            PersonFactory.build(person_eesl_id=11004, first_name="Bob", second_name="Smith")
        )

        result = await person_service.search_persons_with_pagination(
            search_query="John", skip=0, limit=10
        )

        assert len(result.data) == 3
        names = [p.first_name for p in result.data]
        assert "John" in names
        assert "Alice" in names
        assert "Charlie" in names
        assert "Bob" not in names

        full_names = [f"{p.first_name} {p.second_name}" for p in result.data]
        assert "John Doe" in full_names
        assert "Alice Johnson" in full_names
        assert "Charlie Johnson" in full_names
