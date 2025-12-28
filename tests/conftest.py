import os
import pytest
import pytest_asyncio

from src.core import settings

from src.core.models.base import Database, Base

db_url = settings.test_db.test_db_url

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]


# Database fixture that ensures a clean state using transactions, function-scoped
@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Database fixture that ensures a clean state using transactions."""
    db_url_str = str(db_url)
    assert "test" in db_url_str, "Test DB URL must contain 'test'"

    database = Database(db_url_str, echo=False)

    # Create tables at start of each test (faster than migrations)
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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
            # No need to drop tables - transaction rollback cleans up
            pass
