from fastapi import APIRouter, HTTPException
from src.core.models import db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db-pool")
async def get_db_pool_status():
    try:
        pool_status = db.get_pool_status()
        return {
            "status": "healthy",
            "pool": pool_status,
        }
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pool status: {ex}"
        )


@router.get("/db")
async def test_db_connection():
    try:
        await db.test_connection()
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as ex:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {ex}"
        )
