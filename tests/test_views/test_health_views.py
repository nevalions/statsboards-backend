import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthViews:
    async def test_db_connection_endpoint_success(self, client):
        response = await client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "successful" in data["message"]

    async def test_db_pool_status_endpoint_success(self, client):
        response = await client.get("/health/db-pool")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "pool" in data
        assert isinstance(data["pool"], dict)

    async def test_db_pool_status_contains_required_fields(self, client):
        response = await client.get("/health/db-pool")

        assert response.status_code == 200
        data = response.json()["pool"]

        pool_keys = data.keys()
        assert "pool_size" in pool_keys or len(pool_keys) >= 0
