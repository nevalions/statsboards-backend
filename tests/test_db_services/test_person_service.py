import pytest
from fastapi import HTTPException

from src.core.models.base import Database
from src.person.db_services import PersonServiceDB
from src.person.schemas import PersonSchemaCreate, PersonSchemaUpdate
from tests.factories import PersonFactory
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestPersonServiceDBCreateOrUpdate:
    """Test create_or_update_person functionality."""

    async def test_create_person_with_eesl_id(self, test_db: Database):
        """Test creating a person with eesl_id."""
        person_service = PersonServiceDB(test_db)
        person_data = PersonFactory.build(
            person_eesl_id=100, first_name="John", second_name="Doe"
        )

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

        update_data = PersonSchemaUpdate(
            person_eesl_id=400, person_photo_url="http://new.url"
        )

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

        update_data = PersonSchemaUpdate(
            person_eesl_id=500, second_name="Updated"
        )
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
