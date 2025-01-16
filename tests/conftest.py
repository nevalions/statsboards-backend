import subprocess
import pytest
import pytest_asyncio

from src.core import settings
from src.core.models.base import Database, Base


# Apply migrations before each test
@pytest.fixture(scope="function")
def apply_migrations():
    """Apply Alembic migrations before each test."""
    subprocess.run(
        ["alembic", "-x", f"db_url={settings.db.test_db_url}", "upgrade", "head"],
        check=True,
    )
    yield


# Database fixture that ensures a clean state using transactions, function-scoped
@pytest_asyncio.fixture(scope="function")
async def test_db(apply_migrations):
    """Database fixture that ensures a clean state using transactions."""
    assert "test" in settings.db.test_db_url, "Test DB URL must contain 'test'"

    database = Database(settings.db.test_db_url, echo=True)

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


#
# @pytest.mark.usefixtures(scope="session")
# def apply_migrations():
#     """Apply Alembic migrations before tests."""
#     subprocess.run(
#         ["alembic", "-x", f"db_url={settings.db.test_db_url}", "upgrade", "head"],
#         check=True,
#     )
#
#
# @pytest_asyncio.fixture
# async def test_db():
#     """Ensure the database URL is for testing and manage schema."""
#     assert "test" in settings.db.test_db_url, "Test DB URL must contain 'test'"
#
#     database = Database(settings.db.test_db_url, echo=True)
#
#     async with database.engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#     yield database
#
#     async with database.engine.begin() as conn:
#         await conn.rollback()
#
#     await database.close()
