import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.sponsor_lines.views import api_sponsor_line_router
from src.sponsor_lines.db_services import SponsorLineServiceDB
from src.sponsor_lines.schemas import SponsorLineSchemaCreate, SponsorLineSchemaUpdate
from tests.factories import SponsorLineFactory
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(api_sponsor_line_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.mark.asyncio
class TestSponsorLineViews:
    async def test_create_sponsor_line_endpoint(self, client, test_db):
        sponsor_line_data = SponsorLineFactory.build()
        
        response = client.post("/api/sponsor_lines/", json=sponsor_line_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_sponsor_line_endpoint(self, client, test_db):
        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line_data = SponsorLineFactory.build()
        created = await sponsor_line_service.create(sponsor_line_data)
        
        update_data = SponsorLineSchemaUpdate(title="Updated Title")
        
        response = client.put(f"/api/sponsor_lines/", params={"item_id": created.id}, json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_sponsor_line_not_found(self, client):
        update_data = SponsorLineSchemaUpdate(title="Updated Title")
        
        response = client.put(f"/api/sponsor_lines/", params={"item_id": 99999}, json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_sponsor_line_by_id_endpoint(self, client, test_db):
        sponsor_line_service = SponsorLineServiceDB(test_db)
        sponsor_line_data = SponsorLineFactory.build()
        created = await sponsor_line_service.create(sponsor_line_data)
        
        response = client.get(f"/api/sponsor_lines/id/{created.id}/")
        
        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_sponsor_line_by_id_not_found(self, client):
        response = client.get("/api/sponsor_lines/id/99999/")
        
        assert response.status_code == 404

    async def test_get_all_sponsor_lines_endpoint(self, client, test_db):
        sponsor_line_service = SponsorLineServiceDB(test_db)
        await sponsor_line_service.create(SponsorLineFactory.build())
        await sponsor_line_service.create(SponsorLineFactory.build())
        
        response = client.get("/api/sponsor_lines/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_sponsor_line_by_id_with_none_item(self, client, test_db):
        response = client.get("/api/sponsor_lines/id/99999/")
        
        assert response.status_code == 404
