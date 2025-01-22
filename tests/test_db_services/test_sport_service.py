import pytest
from tests.factories import SportFactorySample
from tests.test_data import TestData
from tests.fixtures import test_sport_service, sport


@pytest.fixture(scope="function")
def sample_sport_data():
    return SportFactorySample.build()


@pytest.mark.asyncio
class TestSportServiceDB:
    async def test_create_sport_success(self, test_sport_service, sample_sport_data):
        """Test successful sport creation."""
        created_sport = await test_sport_service.create_sport(sample_sport_data)

        assert created_sport is not None
        assert created_sport.title == sample_sport_data.title
        assert created_sport.description == sample_sport_data.description
        assert created_sport.title == TestData.get_sport_data().title

    async def test_get_sport_by_id(
        self,
        test_sport_service,
        sport,
    ):
        """Test getting a sport by ID."""
        # created_sport = await sport_service.create_sport(sample_sport_data)

        # Now, try to get the sport by its ID
        retrieved_sport = await test_sport_service.get_by_id(sport.id)
        assert sport is not None
        assert sport.title == retrieved_sport.title
        assert sport.description == retrieved_sport.description

    async def test_get_sport_by_id_fail(self, test_sport_service, sport):
        got_sport = await test_sport_service.get_by_id(999)

        assert got_sport is None
