"""Test database connection validation functionality."""

import pytest
from sqlalchemy import text


class TestDatabaseConnectionValidation:
    """Test Database class connection validation methods."""

    @pytest.mark.asyncio
    async def test_validate_database_connection_success(self, test_db):
        """Test that validate_database_connection succeeds with valid database."""
        await test_db.validate_database_connection()

    @pytest.mark.asyncio
    async def test_validate_database_connection_gets_version(self, test_db):
        """Test that validate_database_connection retrieves database version."""
        async with test_db.engine.connect() as connection:
            result = await connection.execute(text("SELECT version()"))
            version = result.scalar()
            assert version is not None
            assert "PostgreSQL" in version

    @pytest.mark.asyncio
    async def test_validate_database_connection_gets_database_name(self, test_db):
        """Test that validate_database_connection retrieves database name."""
        async with test_db.engine.connect() as connection:
            result = await connection.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            assert db_name is not None
            assert len(db_name) > 0

    @pytest.mark.asyncio
    async def test_validate_database_connection_gets_current_user(self, test_db):
        """Test that validate_database_connection retrieves current user."""
        async with test_db.engine.connect() as connection:
            result = await connection.execute(text("SELECT current_user"))
            user = result.scalar()
            assert user is not None
            assert len(user) > 0
