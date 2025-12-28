import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.tournaments.views import api_tournament_router
from src.tournaments.db_services import TournamentServiceDB
from src.tournaments.schemas import TournamentSchemaCreate, TournamentSchemaUpdate
from src.sports.db_services import SportServiceDB
from src.seasons.db_services import SeasonServiceDB
from tests.factories import TournamentFactory, SeasonFactorySample, SportFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.fixture
def test_app():
    app = FastAPI()
    app.include_router(api_tournament_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.mark.asyncio
class TestTournamentViews:
    async def test_create_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        
        response = client.post("/api/tournaments/", json=tournament_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_tournament_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        created = await tournament_service.create_or_update_tournament(tournament_data)
        
        update_data = TournamentSchemaUpdate(title="Updated Title")
        
        response = client.put(f"/api/tournaments/{created.id}/", json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_tournament_not_found(self, client):
        update_data = TournamentSchemaUpdate(title="Updated Title")
        
        response = client.put("/api/tournaments/99999/", json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_tournament_by_eesl_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id, tournament_eesl_id=100)
        created = await tournament_service.create_or_update_tournament(tournament_data)
        
        response = client.get("/api/tournaments/eesl_id/100")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_tournament_by_eesl_id_not_found(self, client):
        response = client.get("/api/tournaments/eesl_id/99999")
        
        assert response.status_code == 404

    async def test_get_teams_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        response = client.get(f"/api/tournaments/id/{tournament.id}/teams/")
        
        assert response.status_code == 200

    async def test_get_players_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        response = client.get(f"/api/tournaments/id/{tournament.id}/players/")
        
        assert response.status_code == 200

    async def test_get_count_of_matches_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        response = client.get(f"/api/tournaments/id/{tournament.id}/matches/count")
        
        assert response.status_code == 200

    async def test_get_matches_by_tournament_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        response = client.get(f"/api/tournaments/id/{tournament.id}/matches/")
        
        assert response.status_code == 200

    async def test_get_all_tournaments_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        await tournament_service.create(TournamentFactory.build(sport_id=sport.id, season_id=season.id))
        
        response = client.get("/api/tournaments/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_tournament_by_id_endpoint(self, client, test_db):
        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())
        
        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())
        
        tournament_service = TournamentServiceDB(test_db)
        tournament_data = TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        created = await tournament_service.create_or_update_tournament(tournament_data)
        
        response = client.get(f"/api/tournaments/id/{created.id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_tournament_by_id_not_found(self, client):
        response = client.get("/api/tournaments/id/99999")
        
        assert response.status_code == 404
