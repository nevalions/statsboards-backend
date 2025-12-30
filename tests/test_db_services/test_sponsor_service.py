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
