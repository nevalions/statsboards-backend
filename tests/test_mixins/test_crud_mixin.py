import pytest
from fastapi import HTTPException

from src.core.models.season import SeasonDB
from src.seasons.db_services import SeasonServiceDB


class TestCRUDMixin:
    """Test suite for CRUDMixin methods."""

    @pytest.mark.asyncio
    async def test_create_success(self, test_db, season_db_model):
        """Test successful creation of an item."""
        service = SeasonServiceDB(test_db)
        created_item = await service.create(season_db_model)
        assert created_item.id is not None
        assert created_item.year == season_db_model.year
        assert created_item.description == season_db_model.description

    @pytest.mark.asyncio
    async def test_create_integrity_error(self, test_db):
        """Test that creating a duplicate item raises IntegrityError."""
        service = SeasonServiceDB(test_db)
        season1 = SeasonDB(year=2024, description="Test Season")
        season2 = SeasonDB(year=2024, description="Test Season 2")
        await service.create(season1)
        with pytest.raises(Exception):
            await service.create(season2)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, test_db, season_db_model):
        """Test successful retrieval of an item by ID."""
        service = SeasonServiceDB(test_db)
        created = await service.create(season_db_model)
        retrieved = await service.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.year == season_db_model.year

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_db):
        """Test retrieval of non-existent item by ID."""
        service = SeasonServiceDB(test_db)
        retrieved = await service.get_by_id(99999)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_by_id_and_model_success(self, test_db, season_db_model):
        """Test successful retrieval of an item by ID and model."""
        service = SeasonServiceDB(test_db)
        created = await service.create(season_db_model)
        retrieved = await service.get_by_id_and_model(SeasonDB, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.year == season_db_model.year

    @pytest.mark.asyncio
    async def test_get_by_id_and_model_not_found(self, test_db):
        """Test retrieval of non-existent item by ID and model."""
        service = SeasonServiceDB(test_db)
        retrieved = await service.get_by_id_and_model(SeasonDB, 99999)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_update_success(self, test_db, season_db_model):
        """Test successful update of an item."""
        service = SeasonServiceDB(test_db)
        from src.seasons.schemas import SeasonSchemaUpdate

        created = await service.create(season_db_model)
        update_data = SeasonSchemaUpdate(
            year=created.year + 1, description="Updated description"
        )
        updated = await service.update(created.id, update_data)
        assert updated is not None
        assert updated.year == created.year + 1
        assert updated.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_non_existent(self, test_db):
        """Test update of non-existent item."""
        service = SeasonServiceDB(test_db)
        from src.seasons.schemas import SeasonSchemaUpdate

        update_data = SeasonSchemaUpdate(year=2025, description="Test")
        updated = await service.update(99999, update_data)
        assert updated is None

    @pytest.mark.asyncio
    async def test_delete_success(self, test_db, season_db_model):
        """Test successful deletion of an item."""
        service = SeasonServiceDB(test_db)
        created = await service.create(season_db_model)
        deleted = await service.delete(created.id)
        assert deleted.id == created.id
        retrieved = await service.get_by_id(created.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, test_db):
        """Test deletion of non-existent item."""
        service = SeasonServiceDB(test_db)
        with pytest.raises(HTTPException) as exc_info:
            await service.delete(99999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_elements(self, test_db, season_db_model):
        """Test retrieval of all elements."""
        service = SeasonServiceDB(test_db)
        from src.core.models.season import SeasonDB

        season_db_model2 = SeasonDB(year=2025, description="Test description 2")
        await service.create(season_db_model)
        await service.create(season_db_model2)
        all_items = await service.get_all_elements()
        assert len(all_items) >= 2
