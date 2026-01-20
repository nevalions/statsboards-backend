"""Test health endpoints."""

import pytest

from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_db_pool_status_success(self, client: AsyncClient):
        """Test successful DB pool status check."""
        response = await client.get("/health/db-pool")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "pool" in data

    @pytest.mark.asyncio
    async def test_db_connection_success(self, client: AsyncClient):
        """Test successful DB connection check."""
        response = await client.get("/health/db")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert data["message"] == "Database connection successful"
