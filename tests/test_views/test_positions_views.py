import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.positions.views import api_position_router
from src.positions.db_services import PositionServiceDB
from src.positions.schemas import PositionSchemaCreate, PositionSchemaUpdate
from src.sports.db_services import SportServiceDB
from tests.factories import SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(api_position_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.mark.asyncio
class TestPositionViews:
    async def test_create_position_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        
        response = client.post("/api/positions/", json=position_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_position_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)
        
        update_data = PositionSchemaUpdate(title="Updated Position")
        
        response = client.put(f"/api/positions/{created.id}/", json=update_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Position"

    async def test_update_position_not_found(self, client):
        update_data = PositionSchemaUpdate(title="Updated Position")
        
        response = client.put("/api/positions/99999/", json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_position_by_title_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)
        
        response = client.get("/api/positions/title/Quarterback/")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_all_positions_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        position_service = PositionServiceDB(test_db)
        await position_service.create(PositionSchemaCreate(title="Quarterback", sport_id=sport.id))
        await position_service.create(PositionSchemaCreate(title="Running Back", sport_id=sport.id))
        
        response = client.get("/api/positions/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_position_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        position_service = PositionServiceDB(test_db)
        position_data = PositionSchemaCreate(title="Quarterback", sport_id=sport.id)
        created = await position_service.create(position_data)
        
        response = client.get(f"/api/positions/id/{created.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_position_by_id_not_found(self, client):
        response = client.get("/api/positions/id/99999")
        
        assert response.status_code == 404
