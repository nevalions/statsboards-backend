import pytest
from tests.factories import SportFactorySample
from tests.fixtures import test_sport_service, sport, test_season_service
from tests.testhelpers import assert_sport_equal


@pytest.fixture(scope="function")
def sport_sample():
    return SportFactorySample.build()


@pytest.mark.asyncio
class TestSportServiceDB:
    async def test_create_sport_success(
        self,
        test_sport_service,
        sport_sample,
    ):
        """Test successful sport creation."""
        created_sport = await test_sport_service.create_sport(sport_sample)
        assert_sport_equal(sport_sample, created_sport)

    async def test_get_sport_by_id(
        self,
        test_sport_service,
        sport,
    ):
        """Test getting a sport by ID."""
        got_sport = await test_sport_service.get_by_id(sport.id)
        assert_sport_equal(sport, got_sport)

    async def test_get_sport_by_id_fail(
        self,
        test_sport_service,
        sport,
        sport_sample,
    ):
        await test_sport_service.create_sport(sport_sample)
        got_sport = await test_sport_service.get_by_id(0)

        assert got_sport is None
