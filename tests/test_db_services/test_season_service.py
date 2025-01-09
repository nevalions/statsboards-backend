import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError

from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate


@pytest_asyncio.fixture(scope="function")
async def season_service(test_db):
    """Fixture to provide an instance of SeasonServiceDB with session."""
    service = SeasonServiceDB(test_db)
    return service


@pytest_asyncio.fixture
async def sample_season_data():
    """Fixture to provide sample season data."""
    return SeasonSchemaCreate(year=2025, description="Test Season")


@pytest.mark.asyncio
class TestSeasonServiceDB:
    async def test_create_season_success(self, season_service, sample_season_data):
        """Test successful season creation."""
        created_season = await season_service.create_season(sample_season_data)

        assert created_season is not None
        assert created_season.year == sample_season_data.year
        assert created_season.description == sample_season_data.description

    async def test_create_season_duplicate_year(
        self, season_service, sample_season_data
    ):
        """Test creating seasons with duplicate years raises PostgreSQL unique constraint error."""
        # Create first season
        await season_service.create_season(sample_season_data)

        # Attempt to create another season with the same year
        duplicate_season = SeasonSchemaCreate(
            year=sample_season_data.year, description="Another Test Season"
        )

        # PostgreSQL will raise IntegrityError for unique constraint violation
        with pytest.raises(IntegrityError) as exc_info:
            await season_service.create_season(duplicate_season)
        assert "duplicate key value violates unique constraint" in str(exc_info.value)


# @pytest.fixture
# async def season_service(test_db):
#     """Fixture to provide an instance of SeasonServiceDB."""
#     # Return the actual SeasonServiceDB instance
#     return SeasonServiceDB(test_db)
#
#
# @pytest.mark.asyncio
# async def test_create_season(season_service):
#     """Test creating a season."""
#     season_data = SeasonSchemaCreate(year=2025, description="Test Season")
#     created_season = await season_service.create_season(season_data)
#
#     assert created_season.year == 2025
#     assert created_season.description == "Test Season"


#
# @pytest.mark.asyncio
# async def test_get_season_by_year(season_service):
#     # Test fetching a season by year
#     season_data = SeasonSchemaCreate(year=2025, description="Test Season")
#     await season_service.create_season(season_data)
#
#     fetched_season = await season_service.get_season_by_year(2025)
#     assert fetched_season is not None
#     assert fetched_season.year == 2025
#     assert fetched_season.description == "Test Season"
