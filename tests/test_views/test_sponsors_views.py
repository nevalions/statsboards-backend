import pytest
from src.sponsors.db_services import SponsorServiceDB
from src.sponsors.schemas import SponsorSchemaCreate, SponsorSchemaUpdate
from tests.factories import SponsorFactory
from src.logging_config import setup_logging

setup_logging()


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
        
        response = await client.put(f"/api/sponsors/", params={"item_id": created.id}, json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_sponsor_not_found(self, client):
        update_data = SponsorSchemaUpdate(title="Updated Title")
        
        response = await client.put(f"/api/sponsors/", params={"item_id": 99999}, json=update_data.model_dump())
        
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
