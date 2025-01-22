import pytest
import pytest_asyncio
from fastapi import HTTPException

from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate
from tests.factories import SeasonFactory
from tests.test_data import TestData


# Ensure the test_db fixture is properly used
@pytest_asyncio.fixture(scope="function")
async def season_service(test_db):
    """Fixture to provide an instance of SeasonServiceDB with session."""
    service = SeasonServiceDB(test_db)
    return service


@pytest.fixture(scope="function")
def sample_season_data():
    return SeasonFactory.build()


# # Fixture to provide sample season data
# @pytest.fixture(scope="function")
# def sample_season_data():
#     """Fixture to provide sample season data."""
#     return TestData.get_season_data()


# Fixture to create the season before each test function
@pytest_asyncio.fixture(scope="function")
async def initial_season(season_service, sample_season_data):
    """Fixture to create a season before each test function and return it."""
    season = await season_service.create_season(sample_season_data)
    return season


# Fixture to provide updated season data for update operation
@pytest.fixture(scope="function")
def updated_season_data():
    """Fixture to provide updated season data."""
    return TestData.get_season_data_for_update()


# Test class for SeasonServiceDB
@pytest.mark.asyncio
class TestSeasonServiceDB:
    async def test_create_season_success(self, season_service, sample_season_data):
        """Test successful season creation."""
        created_season = await season_service.create_season(sample_season_data)

        assert created_season is not None
        assert created_season.year == sample_season_data.year
        assert created_season.description == sample_season_data.description
        assert created_season.year != 2020
        assert created_season.year == TestData.get_season_data().year

    async def test_get_season_by_year_success(
        self,
        season_service,
        sample_season_data,
        initial_season,
    ):
        """Test successful retrieval of a season."""
        # Then try to get it
        season = await season_service.get_season_by_year(sample_season_data.year)

        assert season is not None
        assert season.year == sample_season_data.year
        assert season.description == sample_season_data.description
        assert season.year != 2020

    async def test_get_season_by_year_not_found(
        self,
        season_service,
        sample_season_data,
        initial_season,
    ):
        """Test season not found by year."""
        season = await season_service.get_season_by_year(9999)

        assert season is None

    async def test_update_season_success(
        self,
        season_service,
        initial_season,
        updated_season_data,
        # sample_season_data,
    ):
        # created_season = await season_service.create_season(sample_season_data)
        """Test successful season update."""
        # Store the original values before update
        # original_year = initial_season.year
        # original_description = initial_season.description
        #
        original_year = initial_season.year
        original_description = initial_season.description

        # Perform the update
        updated_season = await season_service.update_season(
            item_id=initial_season.id, item=updated_season_data
        )

        # Assert that the update was successful
        assert updated_season is not None
        assert updated_season.year == updated_season_data.year
        assert updated_season.description == updated_season_data.description
        assert updated_season.id == initial_season.id
        assert updated_season.year != original_year
        assert updated_season.year == TestData.get_season_data_for_update().year

        # Reset the season back to its original state
        reset_season_data = SeasonSchemaUpdate(
            year=original_year, description=original_description
        )
        await season_service.update_season(
            item_id=initial_season.id, item=reset_season_data
        )
        reset_season = await season_service.get_season_by_year(initial_season.year)

        # Assert that the season is now in its original state
        assert reset_season is not None
        assert reset_season.year == original_year
        assert reset_season.description == original_description
        assert reset_season.year == TestData.get_season_data().year

    async def test_update_season_failure(
        self,
        season_service,
        initial_season,
        updated_season_data,
    ):
        """Test failure during season update, expect HTTPException."""
        updated_season_data.year = None

        with pytest.raises(HTTPException) as exc_info:
            await season_service.update_season(
                item_id=initial_season.id, item=updated_season_data
            )

        assert exc_info.value.status_code == 409
        assert "Error updating" in exc_info.value.detail
        assert "Check input data" in exc_info.value.detail

    async def test_create_duplicate_season(
        self,
        season_service,
        sample_season_data,
        initial_season,
    ):
        """Test attempting to create a duplicate season."""
        with pytest.raises(HTTPException) as exc_info:
            await season_service.create_season(sample_season_data)

        # Validate the raised exception
        assert isinstance(exc_info.value, HTTPException)

        assert exc_info.value.status_code == 409
        assert "Error creating" in exc_info.value.detail
        assert "Check input data" in exc_info.value.detail

    async def test_get_tournaments_by_year_empty(self, season_service):
        """Test no tournaments found for the year."""
        # Assuming no tournaments for year 9999
        tournaments = await season_service.get_tournaments_by_year(9999)

        assert len(tournaments) == 0
