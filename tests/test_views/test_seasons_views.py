import pytest

from src.seasons.db_services import SeasonServiceDB
from src.seasons.schemas import SeasonSchemaUpdate
from tests.factories import SeasonFactorySample


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

        update_data = SeasonSchemaUpdate(year=2036)

        response = await client.put(
            f"/api/seasons/{created.id}/",
            json=update_data.model_dump(),
        )

        assert response.status_code == 200

    async def test_update_season_not_found(self, client):
        update_data = SeasonSchemaUpdate(year=2037)

        response = await client.put("/api/seasons/99999/", json=update_data.model_dump())

        assert response.status_code == 404

    async def test_get_season_by_id_endpoint(self, client, test_db):
        season_service = SeasonServiceDB(test_db)
        season_data = SeasonFactorySample.build()
        created = await season_service.create(season_data)

        response = await client.get(f"/api/seasons/id/{created.id}/")

        assert response.status_code == 200
        assert response.json()["id"] == created.id

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

        response = await client.get("/api/seasons/paginated")

        assert response.status_code == 200
        assert len(response.json()["data"]) >= 2

    async def test_get_season_by_id_not_found(self, client):
        response = await client.get("/api/seasons/id/99999/")
        assert response.status_code == 404

    async def test_search_seasons_paginated_success(self, client, test_db):
        """Test search seasons with pagination returns correct data."""
        season_service = SeasonServiceDB(test_db)
        for i in range(5):
            await season_service.create(SeasonFactorySample.build(year=2023 + i))

        response = await client.get("/api/seasons/paginated?page=1&items_per_page=2")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert len(data["data"]) == 2
        assert data["metadata"]["page"] == 1
        assert data["metadata"]["items_per_page"] == 2

    async def test_search_seasons_paginated_search(self, client, test_db):
        """Test search query filters results correctly."""
        season_service = SeasonServiceDB(test_db)
        await season_service.create(
            SeasonFactorySample.build(year=2023, description="Alpha Season")
        )
        await season_service.create(SeasonFactorySample.build(year=2024, description="Beta Season"))
        await season_service.create(
            SeasonFactorySample.build(year=2040, description="Gamma Season")
        )

        response = await client.get("/api/seasons/paginated?search=Alpha&page=1&items_per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        descriptions = [s["description"] for s in data["data"]]
        assert "Alpha Season" in descriptions

    async def test_search_seasons_paginated_empty_search(self, client, test_db):
        """Test empty search query returns all seasons."""
        season_service = SeasonServiceDB(test_db)
        await season_service.create(SeasonFactorySample.build(year=2023))
        await season_service.create(SeasonFactorySample.build(year=2024))

        response = await client.get("/api/seasons/paginated?search=&page=1&items_per_page=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_search_seasons_paginated_ordering(self, client, test_db):
        """Test ordering parameters work correctly."""
        season_service = SeasonServiceDB(test_db)
        for year in [2029, 2030, 2031]:
            await season_service.create(SeasonFactorySample.build(year=year))

        response = await client.get(
            "/api/seasons/paginated?order_by=year&ascending=true&page=1&items_per_page=10"
        )

        assert response.status_code == 200
        data = response.json()
        years = [s["year"] for s in data["data"]]
        assert years == [2029, 2030, 2031]

    async def test_search_seasons_paginated_invalid_page(self, client):
        """Test paginated endpoint rejects invalid page number."""
        response = await client.get("/api/seasons/paginated?page=0&items_per_page=10")

        assert response.status_code == 422

    async def test_search_seasons_paginated_invalid_items_per_page(self, client):
        """Test paginated endpoint rejects invalid items_per_page."""
        response = await client.get("/api/seasons/paginated?page=1&items_per_page=101")

        assert response.status_code == 422
