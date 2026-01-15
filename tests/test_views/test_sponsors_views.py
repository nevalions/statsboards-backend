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

        response = await client.put(
            "/api/sponsors/99999/", json=update_data.model_dump()
        )

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

        response = await client.get("/api/sponsors/")

        assert response.status_code == 200
        assert len(response.json()) >= 2

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
