import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.player.views import api_player_router
from src.player.db_services import PlayerServiceDB
from src.player.schemas import PlayerSchemaCreate, PlayerSchemaUpdate
from src.sports.db_services import SportServiceDB
from src.person.db_services import PersonServiceDB
from tests.factories import SportFactorySample, PersonFactory
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(api_player_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.mark.asyncio
class TestPlayerViews:
    async def test_create_player_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())
        
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        
        response = client.post("/api/players/", json=player_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_get_player_by_eesl_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build(person_eesl_id=100))
        
        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id, player_eesl_id=100)
        created = await player_service.create_or_update_player(player_data)
        
        response = client.get("/api/players/eesl_id/100")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_player_by_eesl_id_not_found(self, client):
        response = client.get("/api/players/eesl_id/99999")
        
        assert response.status_code == 404

    async def test_update_player_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())
        
        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)
        
        update_data = PlayerSchemaUpdate(player_eesl_id=200)
        
        response = client.put(f"/api/players/{created.id}/", json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_get_all_players_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person1 = await person_service.create_or_update_person(PersonFactory.build())
        person2 = await person_service.create_or_update_person(PersonFactory.build())
        
        player_service = PlayerServiceDB(test_db)
        await player_service.create_or_update_player(PlayerSchemaCreate(sport_id=sport.id, person_id=person1.id))
        await player_service.create_or_update_player(PlayerSchemaCreate(sport_id=sport.id, person_id=person2.id))
        
        response = client.get("/api/players/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_player_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())
        
        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)
        
        response = client.get(f"/api/players/id/{created.id}")
        
        assert response.status_code == 200

    async def test_get_player_by_id_not_found(self, client):
        response = client.get("/api/players/id/99999")
        
        assert response.status_code == 404

    async def test_get_person_by_player_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        person_service = PersonServiceDB(test_db)
        person = await person_service.create_or_update_person(PersonFactory.build())
        
        player_service = PlayerServiceDB(test_db)
        player_data = PlayerSchemaCreate(sport_id=sport.id, person_id=person.id)
        created = await player_service.create_or_update_player(player_data)
        
        response = client.get(f"/api/players/id/{created.id}/person")
        
        assert response.status_code == 200
