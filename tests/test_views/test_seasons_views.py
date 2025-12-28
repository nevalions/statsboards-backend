import pytest
from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaCreate, SeasonSchemaUpdate
from tests.factories import SeasonFactorySample
from src.logging_config import setup_logging

setup_logging()


@pytest.mark.asyncio
class TestSeasonViews:
    async def test_create_season_endpoint(self, client, test_db):
        season_data = SeasonFactorySample.build()
        
        response = await client.post("/api/seasons/", json=season_data.model_dump())
        
        assert response.status_code == 200
        assert response.json()["id"] > 0

    async def test_update_season_endpoint(self, client, test_db):
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build()
        created = await season_service.create(season_data)
        
        update_data = SeasonSchemaUpdate(year=2025)
        
        response = await client.put(f"/api/seasons/", params={"item_id": created.id}, json=update_data.model_dump())
        
        assert response.status_code == 200

    async def test_update_season_not_found(self, client):
        update_data = SeasonSchemaUpdate(year=2025)
        
        response = await client.put(f"/api/seasons/", params={"item_id": 99999}, json=update_data.model_dump())
        
        assert response.status_code == 404

    async def test_get_season_by_id_endpoint(self, client, test_db):
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build()
        created = await season_service.create(season_data)
        
        response = await client.get(f"/api/seasons/id/{created.id}/")
        
        assert response.status_code == 200
        assert response.json()["content"]["id"] == created.id

    async def test_get_season_by_year_endpoint(self, client, test_db):
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build(year=2025)
        created = await season_service.create(season_data)
        
        response = await client.get("/api/seasons/year/2025")
        
        assert response.status_code == 200
        assert response.json()["id"] == created.id

    async def test_get_season_by_year_not_found(self, client):
        response = await client.get("/api/seasons/year/9999")
        
        assert response.status_code == 404

    async def test_get_all_seasons_endpoint(self, client, test_db):
        season_service = SeasonServiceDB(test_db)
        await season_service.create(SeasonFactorySample.build(year=2023))
        await season_service.create(SeasonFactorySample.build(year=2024))
        
        response = await client.get("/api/seasons/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 2

    async def test_get_season_by_id_not_found(self, client):
        response = await client.get("/api/seasons/id/99999/")
        
        assert response.status_code == 404
