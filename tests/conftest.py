import os
import subprocess
import sys
import pytest
import pytest_asyncio

from src.core import settings

from src.core.models.base import Database, Base

db_url = settings.test_db.test_db_url

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]


# Apply migrations before each test
@pytest.fixture(scope="function")
def apply_migrations():
    """Apply Alembic migrations before each test."""
    alembic_path = os.path.join(os.path.dirname(sys.executable), "alembic")
    subprocess.run(
        [alembic_path, "-x", f"db_url={db_url}", "upgrade", "head"],
        check=True,
    )
    yield


# Database fixture that ensures a clean state using transactions, function-scoped
@pytest_asyncio.fixture(scope="function")
async def test_db(apply_migrations):
    """Database fixture that ensures a clean state using transactions."""
    db_url_str = str(db_url)
    assert "test" in db_url_str, "Test DB URL must contain 'test'"

    database = Database(db_url_str, echo=False)  # Disable echo for speed

    # Create tables at the start of each test
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Use a transactional connection for tests
    async with database.engine.connect() as connection:
        transaction = await connection.begin()
        database.async_session.configure(bind=connection)

        try:
            yield database
            if transaction.is_active:
                await transaction.rollback()
        finally:
            # Cleanup after the test: drop tables or reset the state
            async with database.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

    # Dispose of the engine after all tests
    await database.close()
