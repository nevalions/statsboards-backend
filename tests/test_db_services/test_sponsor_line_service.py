import pytest
from fastapi import HTTPException

from src.sponsor_lines.schemas import SponsorLineSchemaUpdate
from tests.factories import SponsorLineFactory
from tests.testhelpers import (
    assert_http_exception_on_delete,
)


@pytest.fixture(scope="function")
def sponsor_line_sample():
    return SponsorLineFactory.build()


@pytest.mark.asyncio
class TestSponsorLineServiceDB:
    async def test_create_sponsor_line_success(
        self,
        test_sponsor_line_service,
        sponsor_line_sample,
    ):
        """Test successful sponsor line creation."""
        created_sponsor_line = await test_sponsor_line_service.create(
            sponsor_line_sample
        )
        assert created_sponsor_line.title == sponsor_line_sample.title

    async def test_get_sponsor_line_by_id(
        self,
        test_sponsor_line_service,
        sponsor_line,
    ):
        """Test getting a sponsor line by ID."""
        got_sponsor_line = await test_sponsor_line_service.get_by_id(sponsor_line.id)
        assert got_sponsor_line.id == sponsor_line.id
        assert got_sponsor_line.title == sponsor_line.title

    async def test_get_sponsor_line_by_id_fail(
        self,
        test_sponsor_line_service,
    ):
        """Test fail getting a sponsor line by ID."""
        got_sponsor_line = await test_sponsor_line_service.get_by_id(0)

        assert got_sponsor_line is None

    async def test_update_sponsor_line_success(
        self,
        test_sponsor_line_service,
        sponsor_line,
    ):
        """Test successful sponsor line update."""
        updated_data = SponsorLineSchemaUpdate(title="Updated Sponsor Line")
        updated_sponsor_line = await test_sponsor_line_service.update(
            sponsor_line.id, updated_data
        )

        assert updated_sponsor_line.title == "Updated Sponsor Line"

    async def test_update_sponsor_line_partial_fields(
        self,
        test_sponsor_line_service,
        sponsor_line,
    ):
        """Test partial field update for sponsor line."""
        updated_data = SponsorLineSchemaUpdate(is_visible=True)
        updated_sponsor_line = await test_sponsor_line_service.update(
            sponsor_line.id, updated_data
        )

        assert updated_sponsor_line.is_visible is True

    async def test_delete_sponsor_line_success(
        self,
        test_sponsor_line_service,
        sponsor_line,
    ):
        """Test successful sponsor line deletion"""
        assert sponsor_line is not None
        await test_sponsor_line_service.delete(sponsor_line.id)
        got_sponsor_line = await test_sponsor_line_service.get_by_id(sponsor_line.id)
        assert got_sponsor_line is None

    async def test_delete_sponsor_line_fail(
        self,
        test_sponsor_line_service,
        sponsor_line,
    ):
        """Test fail sponsor line deletion"""
        with pytest.raises(HTTPException) as exc_info:
            await test_sponsor_line_service.delete(sponsor_line.id + 1)
        assert_http_exception_on_delete(exc_info)

    async def test_search_sponsor_lines_with_pagination_success(
        self,
        test_sponsor_line_service,
    ):
        """Test search sponsor lines with pagination returns correct results."""
        for _ in range(5):
            await test_sponsor_line_service.create(SponsorLineFactory.build())

        result = await test_sponsor_line_service.search_sponsor_lines_with_pagination(
            skip=0,
            limit=2,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 2
        assert result.metadata.page == 1
        assert result.metadata.items_per_page == 2
        assert result.metadata.total_items >= 5
        assert result.metadata.total_pages >= 3
        assert result.metadata.has_next is True
        assert result.metadata.has_previous is False

    async def test_search_sponsor_lines_with_pagination_search_query(
        self,
        test_sponsor_line_service,
    ):
        """Test search sponsor lines with query filters correctly."""
        await test_sponsor_line_service.create(SponsorLineFactory.build(title="Test Line Alpha"))
        await test_sponsor_line_service.create(SponsorLineFactory.build(title="Test Line Beta"))
        await test_sponsor_line_service.create(SponsorLineFactory.build(title="Other Line"))

        result = await test_sponsor_line_service.search_sponsor_lines_with_pagination(
            search_query="Test",
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 2
        assert result.data[0].title == "Test Line Alpha"
        assert result.data[1].title == "Test Line Beta"
        assert result.metadata.total_items == 2
