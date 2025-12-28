import pytest
from src.positions.schemas import PositionSchemaCreate, PositionSchemaUpdate
from tests.factories import PositionFactory
from tests.fixtures import (
    test_position_service,
    position,
    sport,
)
from tests.testhelpers import (
    assert_http_exception_on_delete,
    assert_http_exception_on_update,
)


@pytest.fixture(scope="function")
def position_sample():
    return PositionFactory.build()


@pytest.mark.asyncio
class TestPositionServiceDB:
    async def test_create_position_success(
        self,
        test_position_service,
        sport,
        position_sample,
    ):
        """Test successful position creation."""
        position_sample.sport_id = sport.id
        created_position = await test_position_service.create(position_sample)
        assert created_position.title == position_sample.title.upper()
        assert created_position.sport_id == sport.id

    async def test_get_position_by_id(
        self,
        test_position_service,
        position,
    ):
        """Test getting a position by ID."""
        got_position = await test_position_service.get_by_id(position.id)
        assert got_position.id == position.id
        assert got_position.title == position.title

    async def test_get_position_by_id_fail(
        self,
        test_position_service,
    ):
        """Test fail getting a position by ID."""
        got_position = await test_position_service.get_by_id(0)

        assert got_position is None

    async def test_update_position_success(
        self,
        test_position_service,
        position,
    ):
        """Test successful position update."""
        from tests.test_data import TestData

        updated_data = TestData.get_position_data_for_update()
        updated_position = await test_position_service.update(position.id, updated_data)

        assert updated_position.title == updated_data.title

    async def test_update_position_partial_fields(
        self,
        test_position_service,
        position,
    ):
        """Test partial field update for position."""
        updated_data = PositionSchemaUpdate(title="Updated Position")
        updated_position = await test_position_service.update(position.id, updated_data)

        assert updated_position.title == "Updated Position"

    async def test_delete_position_success(
        self,
        test_position_service,
        position,
    ):
        """Test successful position deletion"""
        assert position is not None
        await test_position_service.delete(position.id)
        got_position = await test_position_service.get_by_id(position.id)
        assert got_position is None

    async def test_delete_position_fail(
        self,
        test_position_service,
        position,
    ):
        """Test fail position deletion"""
        assert_http_exception_on_delete(
            await test_position_service.delete(position.id + 1)
        )
