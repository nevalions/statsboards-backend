import pytest
from fastapi import HTTPException

from src.seasons.schemas import SeasonSchemaUpdate
from tests.factories import SeasonFactorySample
from tests.test_data import TestData
from tests.fixtures import (
    test_season_service,
    test_sport_service,
    test_tournament_service,
    season,
    sport,
    tournament,
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
        created_season = await test_season_service.create_season(season_sample)

        assert created_season is not None
        assert created_season.year == season_sample.year
        assert created_season.description == season_sample.description
        assert created_season.year != 2020
        assert created_season.year == TestData.get_season_data().year

    async def test_get_season_by_id_success(
        self,
        test_season_service,
        season,
    ):
        """Test successful retrieval of a season."""
        got_season = await test_season_service.get_by_id(season.id)

        assert got_season is not None
        assert got_season.year == season.year
        assert got_season.description == season.description
        assert got_season.year != 2020

    async def test_get_season_by_id_not_found(
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

        assert got_season is not None
        assert got_season.year == season.year
        assert got_season.description == season.description
        assert got_season.year != 2020

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
        # created_season = await season_service.create_season(season_sample)

        original_year = season.year
        original_description = season.description

        # Perform the update
        updated_season = await test_season_service.update_season(
            item_id=season.id, item=updated_season_data
        )

        # Assert that the update was successful
        assert updated_season is not None
        assert updated_season.year == updated_season_data.year
        assert updated_season.description == updated_season_data.description
        assert updated_season.id == season.id
        assert updated_season.year != original_year
        assert updated_season.year == TestData.get_season_data_for_update().year

        # Reset the season back to its original state
        reset_season_data = SeasonSchemaUpdate(
            year=original_year, description=original_description
        )
        await test_season_service.update_season(
            item_id=season.id, item=reset_season_data
        )
        reset_season = await test_season_service.get_season_by_year(season.year)

        # Assert that the season is now in its original state
        assert reset_season is not None
        assert reset_season.year == original_year
        assert reset_season.description == original_description
        assert reset_season.year == TestData.get_season_data().year

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

        # Validate the raised exception
        assert isinstance(exc_info.value, HTTPException)

        assert exc_info.value.status_code == 409
        assert "Error creating" in exc_info.value.detail
        assert "Check input data" in exc_info.value.detail

    async def test_get_one_tournament_by_year(
        self,
        test_season_service,
        tournament,
    ):
        """Test tournaments for the year."""
        season_id = tournament.season_id
        got_season = await test_season_service.get_by_id(season_id)
        tournaments = await test_season_service.get_tournaments_by_year(got_season.year)

        assert len(tournaments) == 1
