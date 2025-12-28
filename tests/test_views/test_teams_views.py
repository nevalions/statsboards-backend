import pytest
from src.teams.db_services import TeamServiceDB
from src.teams.schemas import TeamSchemaCreate
from src.sports.db_services import SportServiceDB
from tests.factories import TeamFactory, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestTeamViews:
    async def test_create_team_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        team_data = TeamFactory.build(sport_id=sport.id)
        
        response = await client.post("/api/teams/", json=team_data.model_dump())
        
        assert response.status_code == 400
        assert "Error creating new team" in response.json()["detail"]

    async def test_get_team_by_eesl_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        team_service = TeamServiceDB(test_db)
        team_data = TeamFactory.build(sport_id=sport.id, team_eesl_id=100)
        created = await team_service.create_or_update_team(team_data)
        
        response = await client.get(f"/api/teams/eesl_id/100")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_team_by_eesl_id_not_found(self, client):
        response = await client.get("/api/teams/eesl_id/99999")
        
        assert response.status_code == 404

    async def test_update_team_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        team_service = TeamServiceDB(test_db)
        team_data = TeamFactory.build(sport_id=sport.id)
        created = await team_service.create_or_update_team(team_data)
        
        update_data = {"title": "Updated Title"}
        
        response = await client.put(f"/api/teams/{created.id}/", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_get_all_teams_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        team_service = TeamServiceDB(test_db)
        await team_service.create(TeamFactory.build(sport_id=sport.id))
        await team_service.create(TeamFactory.build(sport_id=sport.id))
        
        response = await client.get("/api/teams/")
        
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_get_team_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        team_service = TeamServiceDB(test_db)
        team_data = TeamFactory.build(sport_id=sport.id)
        created = await team_service.create_or_update_team(team_data)
        
        response = await client.get(f"/api/teams/id/{created.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_team_by_id_not_found(self, client):
        response = await client.get("/api/teams/id/99999")
        
        assert response.status_code == 404
