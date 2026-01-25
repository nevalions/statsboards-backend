from typing import Any

from fastapi import APIRouter, HTTPException

from src.core.service_registry import get_service_registry

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db-pool")
async def get_db_pool_status() -> dict[str, Any]:
    try:
        registry = get_service_registry()
        pool_status = registry.database.get_pool_status()
        return {
            "status": "healthy",
            "pool": pool_status,
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Failed to get pool status: {ex}") from ex


@router.get("/db")
async def test_db_connection() -> dict[str, str]:
    try:
        registry = get_service_registry()
        await registry.database.test_connection()
        return {"status": "healthy", "message": "Database connection successful"}
    except Exception as ex:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {ex}") from ex
