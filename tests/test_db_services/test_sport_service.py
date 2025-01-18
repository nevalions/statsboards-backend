import pytest
import pytest_asyncio

from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate, SportSchemaUpdate
from tests.factories import SportFactory


@pytest_asyncio.fixture(scope="function")
async def sport_service(test_db) -> SportServiceDB:
    """Fixture to provide an instance of SportServiceDB with session."""
    service = SportServiceDB(test_db)  # Pass the engine or async session
    return service


# @pytest.fixture(scope="function")
# def sample_sport_data():
#     """Fixture to provide sample sport data."""
#     return SportSchemaCreate(title="Football", description="American Football")


@pytest.fixture(scope="function")
def sample_sport_data():
    """Fixture to generate sport data using a factory."""
    return SportFactory.build()


@pytest.mark.asyncio
class TestSportServiceDB:
    async def test_create_sport_success(self, sport_service, sample_sport_data):
        """Test successful sport creation."""
        created_sport = await sport_service.create_sport(sample_sport_data)

        assert created_sport is not None
        assert created_sport.title == sample_sport_data.title
        assert created_sport.description == sample_sport_data.description

    async def test_get_sport_by_id(self, sport_service, sample_sport_data):
        """Test getting a sport by ID."""
        created_sport = await sport_service.create_sport(sample_sport_data)

        # Now, try to get the sport by its ID
        retrieved_sport = await sport_service.get_by_id(created_sport.id)
        assert created_sport is not None
        assert created_sport.title == retrieved_sport.title
        assert created_sport.description == retrieved_sport.description

    async def test_get_sport_by_id_fail(self, sport_service, sample_sport_data):
        sport = await sport_service.get_by_id(999)

        assert sport is None
