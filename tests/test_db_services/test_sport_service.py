import pytest

from src.sports.schemas import SportSchemaCreate
from src.tournaments.schemas import TournamentSchemaCreate
from tests.factories import SportFactorySample
from tests.testhelpers import assert_sport_equal, assert_tournaments_equal


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
        created_sport: SportSchemaCreate = await test_sport_service.create(sport_sample)
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
        """Test fail getting a sport by ID."""
        await test_sport_service.create(sport_sample)
        got_sport = await test_sport_service.get_by_id(0)

        assert got_sport is None

    async def test_get_tournaments_by_sport(
        self,
        test_sport_service,
        sport,
        season,
        tournaments,
        test_tournament_service,
        test_season_service,
    ):
        """Test getting tournaments by sport."""
        got_tournaments: list[
            TournamentSchemaCreate
        ] = await test_sport_service.get_tournaments_by_sport(sport.id)

        assert_tournaments_equal(tournaments, got_tournaments)
