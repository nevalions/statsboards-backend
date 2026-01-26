"""
Tests for main application module.

Run with:
    pytest tests/test_main.py
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI


@pytest.fixture
def mock_settings():
    """Mock settings."""
    with patch("src.main.settings") as mock:
        mock.uploads_path = "/tmp/uploads"
        mock.validate_all = Mock()
        yield mock


@pytest.fixture
def mock_db():
    """Mock database."""
    with patch("src.main.db") as mock:
        mock.validate_database_connection = AsyncMock()
        mock.close = AsyncMock()
        yield mock


@pytest.fixture
def mock_ws_manager():
    """Mock WebSocket manager."""
    with patch("src.main.ws_manager") as mock:
        mock.startup = AsyncMock()
        mock.shutdown = AsyncMock()
        mock.maintain_connection = AsyncMock()
        yield mock


@pytest.fixture
def mock_registry():
    """Mock router registry."""
    with patch("src.main.configure_routers") as mock_configure:
        mock_registry = Mock()
        mock_registry.register_all = Mock()
        mock_configure.return_value = mock_registry
        yield mock_registry


@pytest.mark.asyncio
async def test_lifespan_startup(mock_settings, mock_db, mock_ws_manager, mock_registry):
    """Test lifespan startup."""
    from src.main import lifespan

    app = FastAPI()
    mock_cache_service = Mock()

    with (
        patch("src.main.init_service_registry", Mock()) as mock_init,
        patch("src.main.register_all_services", Mock()) as mock_register,
        patch("src.main.get_service_registry") as mock_get_registry,
    ):
        mock_get_registry.return_value.get.return_value = mock_cache_service
        async with lifespan(app):
            mock_settings.validate_all.assert_called_once()
            mock_init.assert_called_once_with(mock_db)
            mock_register.assert_called_once_with(mock_db)
            mock_db.validate_database_connection.assert_awaited_once()
            mock_ws_manager.startup.assert_awaited_once()
            mock_ws_manager.maintain_connection.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_shutdown(mock_settings, mock_db, mock_ws_manager):
    """Test lifespan shutdown."""
    from src.main import lifespan

    app = FastAPI()
    mock_cache_service = Mock()

    with (
        patch("src.main.init_service_registry", Mock()),
        patch("src.main.register_all_services", Mock()),
        patch("src.main.get_service_registry") as mock_get_registry,
    ):
        mock_get_registry.return_value.get.return_value = mock_cache_service
        async with lifespan(app):
            pass

        mock_db.close.assert_awaited_once()
        mock_ws_manager.shutdown.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_exception_handling(mock_settings, mock_db):
    """Test lifespan exception handling."""
    from src.main import lifespan

    app = FastAPI()

    with patch("src.main.init_service_registry", side_effect=Exception("Test error")):
        with pytest.raises(Exception, match="Test error"):
            async with lifespan(app):
                pass


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    from fastapi.testclient import TestClient

    from src.main import app

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "timestamp" in data


def test_app_initialization(mock_settings, mock_db, mock_ws_manager, mock_registry):
    """Test app initialization with all components."""
    from src.main import app

    assert app is not None
    assert isinstance(app, FastAPI)


def test_cors_middleware_configuration(mock_settings, monkeypatch):
    """Test CORS middleware configuration."""
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")

    from importlib import reload

    from starlette.testclient import TestClient

    import src.main

    reload(src.main)

    client = TestClient(src.main.app)

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert (
        response.status_code == 200 or response.status_code == 404
    )  # May not have OPTIONS handler


def test_static_files_mount(mock_settings):
    """Test static files mount."""
    from src.main import app

    static_mount_found = False
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/static/uploads":
            static_mount_found = True
            break

    assert static_mount_found


@pytest.mark.asyncio
async def test_websocket_in_lifespan(mock_settings, mock_ws_manager):
    """Test WebSocket startup/shutdown in lifespan."""
    from src.main import lifespan

    app = FastAPI()
    mock_cache_service = Mock()

    with (
        patch("src.main.init_service_registry", Mock()),
        patch("src.main.register_all_services", Mock()),
        patch("src.main.get_service_registry") as mock_get_registry,
    ):
        mock_get_registry.return_value.get.return_value = mock_cache_service
        async with lifespan(app):
            pass

        mock_ws_manager.startup.assert_awaited_once()
        mock_ws_manager.shutdown.assert_awaited_once()
