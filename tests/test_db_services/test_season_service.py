import pytest
from fastapi import HTTPException

from src.seasons.schemas import SeasonSchemaUpdate, SeasonSchemaCreate
from tests.factories import SeasonFactorySample
from tests.test_data import TestData
from tests.fixtures import (
    test_season_service,
    test_sport_service,
    test_tournament_service,
    season,
    sport,
    tournament,
    tournaments,
)
from tests.testhelpers import (
    assert_season_equal,
    assert_tournaments_equal,
    assert_http_exception,
    assert_tournament_equal,
)


@pytest.fixture(scope="function")
def season_sample():
    return SeasonFactorySample.build()


# Fixture to provide updated season data for update operation
@pytest.fixture(scope="function")
def updated_season_data():
    """Fixture to provide updated season data."""
    return TestData.get_season_data_for_update()


# Test class for SeasonServiceDB
@pytest.mark.asyncio
class TestSeasonServiceDB:
    async def test_create_season_success(self, test_season_service, season_sample):
        """Test successful season creation."""
        created_season: SeasonSchemaCreate = await test_season_service.create_season(
            season_sample
        )
        assert_season_equal(season_sample, created_season)

    async def test_get_season_by_id_success(
        self,
        test_season_service,
        season,
    ):
        """Test successful retrieval of a season."""
        got_season = await test_season_service.get_by_id(season.id)
        assert_season_equal(season, got_season)

    async def test_get_season_by_id_fail(
        self,
        test_season_service,
        season_sample,
    ):
        """Test season not found by year."""
        await test_season_service.create_season(season_sample)
        got_season = await test_season_service.get_by_id(0)

        assert got_season is None

    async def test_get_season_by_year_success(
        self,
        test_season_service,
        season,
        season_sample,
    ):
        """Test successful retrieval of a season."""
        got_season = await test_season_service.get_season_by_year(season.year)
        assert_season_equal(season, got_season)

    async def test_get_season_by_year_not_found(
        self,
        test_season_service,
        season_sample,
    ):
        """Test season not found by year."""
        got_season = await test_season_service.get_season_by_year(1)

        assert got_season is None

    async def test_update_season_success(
        self,
        test_season_service,
        season,
        updated_season_data,
    ):
        """Test successful season update."""
        updated_season = await test_season_service.update_season(
            item_id=season.id, item=updated_season_data
        )
        assert updated_season is not None
        assert updated_season.year == updated_season_data.year
        assert updated_season.description == updated_season_data.description
        assert updated_season.id == season.id
        assert updated_season.year != season.year
        assert updated_season.year == TestData.get_season_data_for_update().year

        # Reset the season back to its original state
        reset_season_data = SeasonSchemaUpdate(
            year=season.year, description=season.description
        )
        await test_season_service.update_season(
            item_id=season.id, item=reset_season_data
        )
        reset_season = await test_season_service.get_season_by_year(season.year)
        assert_season_equal(season, reset_season)

    async def test_update_season_failure(
        self,
        test_season_service,
        season,
        updated_season_data,
    ):
        """Test failure during season update, expect HTTPException."""
        updated_season_data.year = None
        with pytest.raises(HTTPException) as exc_info:
            await test_season_service.update_season(
                item_id=season.id, item=updated_season_data
            )

        assert exc_info.value.status_code == 409
        assert "Error updating" in exc_info.value.detail
        assert "Check input data" in exc_info.value.detail

    async def test_create_duplicate_season(
        self,
        test_season_service,
        season,
    ):
        """Test attempting to create a duplicate season."""
        with pytest.raises(HTTPException) as exc_info:
            await test_season_service.create_season(season)

        assert_http_exception(exc_info)

    async def test_get_one_tournament_by_year(
        self,
        test_season_service,
        tournament,
        season,
        sport,
    ):
        """Test tournaments for the year."""
        season_id = tournament.season_id
        got_season = await test_season_service.get_by_id(season_id)
        got_tournaments = await test_season_service.get_tournaments_by_year(
            got_season.year
        )

        assert len(got_tournaments) == 1
        assert_tournament_equal(tournament, got_tournaments[0], season, sport)

    async def test_get_tournaments_by_year(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year."""
        season_id = tournaments[0].season_id
        got_season = await test_season_service.get_by_id(season_id)

        fetched_tournaments = await test_season_service.get_tournaments_by_year(
            got_season.year
        )

        assert_tournaments_equal(tournaments, fetched_tournaments)

    async def test_get_tournaments_by_year_and_sport(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year and sport."""
        season_id = tournaments[0].season_id
        sport_id = tournaments[0].sport_id
        got_season = await test_season_service.get_by_id(season_id)

        fetched_tournaments = (
            await test_season_service.get_tournaments_by_year_and_sport(
                year=got_season.year,
                sport_id=sport_id,
            )
        )
        assert_tournaments_equal(tournaments, fetched_tournaments)

    async def test_get_tournaments_by_season_id_and_sport_id(
        self,
        test_season_service,
        tournaments,
    ):
        """Test retrieving tournaments for a given year and sport."""
        season_id = tournaments[0].season_id
        sport_id = tournaments[0].sport_id

        fetched_tournaments = (
            await test_season_service.get_tournaments_by_season_and_sport_ids(
                season_id=season_id,
                sport_id=sport_id,
            )
        )
        assert_tournaments_equal(tournaments, fetched_tournaments)
