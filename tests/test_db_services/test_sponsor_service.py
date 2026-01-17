import pytest
from fastapi import HTTPException

from src.sponsors.schemas import SponsorSchemaUpdate
from tests.factories import SponsorFactory
from tests.testhelpers import (
    assert_http_exception_on_delete,
)


@pytest.fixture(scope="function")
def sponsor_sample():
    return SponsorFactory.build()


@pytest.mark.asyncio
class TestSponsorServiceDB:
    async def test_create_sponsor_success(
        self,
        test_sponsor_service,
        sponsor_sample,
    ):
        """Test successful sponsor creation."""
        created_sponsor = await test_sponsor_service.create(sponsor_sample)
        assert created_sponsor.title == sponsor_sample.title

    async def test_get_sponsor_by_id(
        self,
        test_sponsor_service,
        sponsor,
    ):
        """Test getting a sponsor by ID."""
        got_sponsor = await test_sponsor_service.get_by_id(sponsor.id)
        assert got_sponsor.id == sponsor.id
        assert got_sponsor.title == sponsor.title

    async def test_get_sponsor_by_id_fail(
        self,
        test_sponsor_service,
    ):
        """Test fail getting a sponsor by ID."""
        got_sponsor = await test_sponsor_service.get_by_id(0)

        assert got_sponsor is None

    async def test_update_sponsor_success(
        self,
        test_sponsor_service,
        sponsor,
    ):
        """Test successful sponsor update."""
        from tests.test_data import TestData

        updated_data = TestData.get_sponsor_data_for_update()
        updated_sponsor = await test_sponsor_service.update(sponsor.id, updated_data)

        assert updated_sponsor.title == updated_data.title

    async def test_update_sponsor_partial_fields(
        self,
        test_sponsor_service,
        sponsor,
    ):
        """Test partial field update for sponsor."""
        updated_data = SponsorSchemaUpdate(title="Updated Sponsor")
        updated_sponsor = await test_sponsor_service.update(sponsor.id, updated_data)

        assert updated_sponsor.title == "Updated Sponsor"

    async def test_delete_sponsor_success(
        self,
        test_sponsor_service,
        sponsor,
    ):
        """Test successful sponsor deletion"""
        assert sponsor is not None
        await test_sponsor_service.delete(sponsor.id)
        got_sponsor = await test_sponsor_service.get_by_id(sponsor.id)
        assert got_sponsor is None

    async def test_delete_sponsor_fail(
        self,
        test_sponsor_service,
        sponsor,
    ):
        """Test fail sponsor deletion"""
        with pytest.raises(HTTPException) as exc_info:
            await test_sponsor_service.delete(sponsor.id + 1)
        assert_http_exception_on_delete(exc_info)

    async def test_search_sponsors_with_pagination_success(
        self,
        test_sponsor_service,
    ):
        """Test search sponsors with pagination returns correct results."""
        for i in range(5):
            await test_sponsor_service.create(SponsorFactory.build())

        result = await test_sponsor_service.search_sponsors_with_pagination(
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

    async def test_search_sponsors_with_pagination_search_query(
        self,
        test_sponsor_service,
    ):
        """Test search sponsors with query filters correctly."""
        await test_sponsor_service.create(SponsorFactory.build(title="Test Sponsor Alpha"))
        await test_sponsor_service.create(SponsorFactory.build(title="Test Sponsor Beta"))
        await test_sponsor_service.create(SponsorFactory.build(title="Other Sponsor"))

        result = await test_sponsor_service.search_sponsors_with_pagination(
            search_query="Test",
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 2
        assert result.data[0].title == "Test Sponsor Alpha"
        assert result.data[1].title == "Test Sponsor Beta"
        assert result.metadata.total_items == 2

    async def test_search_sponsors_with_pagination_empty_search(
        self,
        test_sponsor_service,
    ):
        """Test empty search query returns all sponsors."""
        await test_sponsor_service.create(SponsorFactory.build(title="Sponsor A"))
        await test_sponsor_service.create(SponsorFactory.build(title="Sponsor B"))

        result = await test_sponsor_service.search_sponsors_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) >= 2

    async def test_search_sponsors_with_pagination_ordering(
        self,
        test_sponsor_service,
    ):
        """Test ordering works correctly."""
        await test_sponsor_service.create(SponsorFactory.build(title="Alpha Sponsor"))
        await test_sponsor_service.create(SponsorFactory.build(title="Beta Sponsor"))
        await test_sponsor_service.create(SponsorFactory.build(title="Gamma Sponsor"))

        result_desc = await test_sponsor_service.search_sponsors_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        result_asc = await test_sponsor_service.search_sponsors_with_pagination(
            search_query=None,
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=False,
        )

        assert result_desc is not None
        assert result_asc is not None
        titles_desc = [s.title for s in result_desc.data]
        titles_asc = [s.title for s in result_asc.data]
        assert titles_desc == sorted(titles_desc)
        assert titles_asc == sorted(titles_asc, reverse=True)

    async def test_search_sponsors_with_pagination_empty_results(
        self,
        test_sponsor_service,
    ):
        """Test empty results returns empty list."""
        result = await test_sponsor_service.search_sponsors_with_pagination(
            search_query="NonExistent",
            skip=0,
            limit=10,
            order_by="title",
            order_by_two="id",
            ascending=True,
        )

        assert result is not None
        assert len(result.data) == 0
        assert result.metadata.total_items == 0
        assert result.metadata.total_pages == 0
        assert result.metadata.has_next is False
        assert result.metadata.has_previous is False
