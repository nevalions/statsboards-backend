import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.sports.views import api_sport_router
from src.sports.db_services import SportServiceDB
from src.sports.schemas import SportSchemaCreate, SportSchemaUpdate
from tests.factories import SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(api_sport_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.mark.asyncio
class TestSportViews:
    async def test_create_sport_endpoint(self, client, test_db):
        sport_data = SportFactorySample.build()
        
        response = client.post("/api/sports/", json=sport_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport_data = SportFactorySample.build()
        created = await sport_service.create(sport_data)
        
        update_data = SportSchemaUpdate(title="Updated Title")
        
        response = client.put(f"/api/sports/", params={"item_id": created.id}, json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_sport_not_found(self, client):
        update_data = SportSchemaUpdate(title="Updated Title")
        
        response = client.put(f"/api/sports/", params={"item_id": 99999}, json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_sport_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport_data = SportFactorySample.build()
        created = await sport_service.create(sport_data)
        
        response = client.get(f"/api/sports/id/{created.id}/")
        
        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_sport_by_id_not_found(self, client):
        response = client.get("/api/sports/id/99999/")
        
        assert response.status_code == 404

    async def test_get_all_sports_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        await sport_service.create(SportFactorySample.build())
        await sport_service.create(SportFactorySample.build())
        
        response = client.get("/api/sports/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_tournaments_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        response = client.get(f"/api/sports/id/{sport.id}/tournaments")
        
        assert response.status_code == 200

    async def test_get_teams_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        response = client.get(f"/api/sports/id/{sport.id}/teams")
        
        assert response.status_code == 200

    async def test_get_players_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        response = client.get(f"/api/sports/id/{sport.id}/players")
        
        assert response.status_code == 200

    async def test_get_positions_by_sport_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        response = client.get(f"/api/sports/id/{sport.id}/positions")
        
        assert response.status_code == 200
