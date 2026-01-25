from io import BytesIO

import pytest
from PIL import Image

from src.sponsors.db_services import SponsorServiceDB
from src.sponsors.schemas import SponsorSchemaUpdate
from tests.factories import SponsorFactory


def create_test_image():
    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
class TestSponsorViews:
    async def test_create_sponsor_endpoint(self, client, test_db):
        sponsor_data = SponsorFactory.build()

        response = await client.post("/api/sponsors/", json=sponsor_data.model_dump())

        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_sponsor_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_data = SponsorFactory.build()
        created = await sponsor_service.create(sponsor_data)

        update_data = SponsorSchemaUpdate(title="Updated Title")

        response = await client.put(
            f"/api/sponsors/{created.id}/",
            json=update_data.model_dump(),
        )

        assert response.status_code == 200

    async def test_update_sponsor_not_found(self, client):
        update_data = SponsorSchemaUpdate(title="Updated Title")

        response = await client.put("/api/sponsors/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_sponsor_by_id_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        sponsor_data = SponsorFactory.build()
        created = await sponsor_service.create(sponsor_data)

        response = await client.get(f"/api/sponsors/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_sponsor_by_id_not_found(self, client):
        response = await client.get("/api/sponsors/id/99999/")

        assert response.status_code == 404

    async def test_get_all_sponsors_endpoint(self, client, test_db):
        sponsor_service = SponsorServiceDB(test_db)
        await sponsor_service.create(SponsorFactory.build())
        await sponsor_service.create(SponsorFactory.build())

        response = await client.get("/api/sponsors/paginated")

        assert response.status_code == 200
        assert len(response.json()["data"]) >= 2

    async def test_get_sponsor_by_id_with_none_item(self, client, test_db):
        response = await client.get("/api/sponsors/id/99999/")

        assert response.status_code == 404

    async def test_upload_sponsor_logo_endpoint(self, client):
        file_content = create_test_image()
        files = {"file": ("test_logo.png", BytesIO(file_content), "image/png")}
        response = await client.post("/api/sponsors/upload_logo", files=files)

        assert response.status_code == 200
        assert "logoUrl" in response.json()
        assert "sponsors/logos" in response.json()["logoUrl"]

    async def test_upload_sponsor_logo_with_invalid_file(self, client):
        file_content = b"not a valid image"
        files = {"file": ("test_invalid.txt", BytesIO(file_content), "text/plain")}
        response = await client.post("/api/sponsors/upload_logo", files=files)

        assert response.status_code == 400

    async def test_search_sponsors_paginated_success(self, client, test_db):
        """Test search sponsors with pagination returns correct data."""
        sponsor_service = SponsorServiceDB(test_db)
        for i in range(5):
            await sponsor_service.create(SponsorFactory.build())

        response = await client.get("/api/sponsors/paginated?page=1&items_per_page=2")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 2
        assert data["metadata"]["page"] == 1
        assert data["metadata"]["items_per_page"] == 2

    async def test_search_sponsors_paginated_search(self, client, test_db):
        """Test search query filters results correctly."""
        sponsor_service = SponsorServiceDB(test_db)
        await sponsor_service.create(SponsorFactory.build(title="Test Sponsor Alpha"))
        await sponsor_service.create(SponsorFactory.build(title="Test Sponsor Beta"))
        await sponsor_service.create(SponsorFactory.build(title="Other Sponsor"))

        response = await client.get("/api/sponsors/paginated?search=Test&page=1&items_per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        titles = [s["title"] for s in data["data"]]
        assert "Test Sponsor Alpha" in titles
        assert "Test Sponsor Beta" in titles

    async def test_search_sponsors_paginated_empty_search(self, client, test_db):
        """Test empty search query returns all sponsors."""
        sponsor_service = SponsorServiceDB(test_db)
        await sponsor_service.create(SponsorFactory.build(title="Sponsor A"))
        await sponsor_service.create(SponsorFactory.build(title="Sponsor B"))

        response = await client.get("/api/sponsors/paginated?search=&page=1&items_per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_search_sponsors_paginated_ordering(self, client, test_db):
        """Test ordering parameters work correctly."""
        sponsor_service = SponsorServiceDB(test_db)
        for i in range(3):
            await sponsor_service.create(SponsorFactory.build(title=f"Sponsor {i}"))

        response = await client.get(
            "/api/sponsors/paginated?order_by=title&ascending=true&page=1&items_per_page=10"
        )

        assert response.status_code == 200
        data = response.json()
        titles = [s["title"] for s in data["data"]]
        assert titles == sorted(titles)

    async def test_search_sponsors_paginated_invalid_page(self, client):
        """Test paginated endpoint rejects invalid page number."""
        response = await client.get("/api/sponsors/paginated?page=0&items_per_page=10")

        assert response.status_code == 422

    async def test_search_sponsors_paginated_invalid_items_per_page(self, client):
        """Test paginated endpoint rejects invalid items_per_page."""
        response = await client.get("/api/sponsors/paginated?page=1&items_per_page=101")

        assert response.status_code == 422
