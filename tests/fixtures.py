import pytest_asyncio
from tests.factories import SportFactorySample, SeasonFactorySample
from tests.testhelpers import create_test_entity


@pytest_asyncio.fixture
async def sport(test_db):
    """Create and return a sport instance in the database."""
    return await create_test_entity(SportFactorySample, test_db)


@pytest_asyncio.fixture
async def season(test_db):
    """Create and return a season instance in the database."""
    return await create_test_entity(SeasonFactorySample, test_db)
