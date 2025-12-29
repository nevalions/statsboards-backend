import os
import shutil
import pytest
import pytest_asyncio
from unittest.mock import patch

from src.core import settings

from src.core.models.base import Database, Base

db_url = settings.test_db.test_db_url

# Import fixtures from fixtures.py
pytest_plugins = ["tests.fixtures"]

# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks test as integration test (hits real website)"
    )

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


@pytest.fixture(scope="session")
def test_downloads_dir():
    """Fixture to create and clean up test downloads directory."""
    downloads_dir = os.path.join(os.path.dirname(__file__), "test_downloads")

    # Create directory before tests
    os.makedirs(downloads_dir, exist_ok=True)

    yield downloads_dir

    # Clean up after all tests complete
    if os.path.exists(downloads_dir):
        shutil.rmtree(downloads_dir)
        print(f"\nCleaned up test downloads directory: {downloads_dir}")


@pytest.fixture
def test_uploads_path(test_downloads_dir, monkeypatch):
    """Fixture to patch uploads_path for integration tests."""
    import src.core.config
    monkeypatch.setattr(src.core.config, "uploads_path", test_downloads_dir)
    return test_downloads_dir
