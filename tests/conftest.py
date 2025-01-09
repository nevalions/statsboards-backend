import subprocess
import pytest
import pytest_asyncio

from src.core.config import TestDbSettings
from src.core.models.base import Database, Base


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations before tests."""
    test_settings = TestDbSettings()
    db_url = test_settings.db_url
    subprocess.run(
        ["alembic", "-x", f"db_url={db_url}", "upgrade", "head"],
        check=True,
    )


@pytest_asyncio.fixture
async def test_db():
    # Create the test database instance
    test_settings = TestDbSettings()
    database = Database(test_settings.db_url, echo=True)

    # Create tables
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield database

    # Drop tables and dispose of the engine
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await database.close()
