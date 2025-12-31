"""Main FastAPI application entry point."""

import logging.config
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.core.config import settings, uploads_path
from src.core.exception_handler import register_exception_handlers
from src.core.models.base import db
from src.core.service_registry import init_service_registry
from src.core.service_initialization import register_all_services
from src.utils.websocket.websocket_manager import ws_manager
from src.core.router_registry import RouterRegistry, configure_routers
from src.logging_config import logs_dir, setup_logging

logger = logging.getLogger("backend_logger_fastapi")
db_logger = logging.getLogger("backend_logger_base_db")
setup_logging()

log_file_path = logs_dir / "backend.log"
if os.access(log_file_path, os.W_OK):
    logger.debug("Log file is writable.")
else:
    logger.error("Log file is not writable.")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Args:
        _app (FastAPI): The FastAPI application instance (unused).
    """
    db_logger.info("Starting application lifespan.")
    try:
        settings.validate_all()
        init_service_registry(db)
        register_all_services(db)
        logger.info("Service registry initialized and all services registered")
        await db.validate_database_connection()
        yield
    except Exception as ex:
        db_logger.critical(f"Critical error during startup: {ex}", exc_info=True)
        raise ex
    finally:
        db_logger.info("Shutting down application lifespan after test connection.")
        await db.close()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Status information including timestamp.
    """
    current_time = datetime.now(timezone.utc).isoformat()
    return {
        "status": "ok",
        "service": "FastAPI Backend is running",
        "timestamp": current_time,
    }


registry = configure_routers(RouterRegistry())
registry.register_all(app)

# Add these event handlers in your startup code
app.add_event_handler("startup", ws_manager.startup)
app.add_event_handler("shutdown", ws_manager.shutdown)

logger.info("FastAPI app initialized.")
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [allowed_origins] if allowed_origins == "*" else allowed_origins.split(",")
logger.info(f"allowed_origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static/uploads",
    StaticFiles(directory=uploads_path),
    name="uploads",
)
