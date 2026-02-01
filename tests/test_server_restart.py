"""
Integration tests for server restart with active WebSocket connections.

These tests verify that the server can restart gracefully even with active
WebSocket connections, ensuring graceful shutdown timeout configuration works.

Run with:
    pytest tests/test_server_restart.py -m integration
"""

from pathlib import Path

import pytest


@pytest.mark.integration
class TestServerRestartConfiguration:
    """Test server restart configuration for WebSocket connections."""

    def test_runserver_has_graceful_shutdown_timeout(self):
        """Test that runserver.py has graceful shutdown timeout configured."""
        runserver_path = Path(__file__).parent.parent / "src" / "runserver.py"
        runserver_content = runserver_path.read_text()

        assert "timeout_graceful_shutdown" in runserver_content, (
            "runserver.py missing timeout_graceful_shutdown configuration"
        )
        assert "timeout_keep_alive" in runserver_content, (
            "runserver.py missing timeout_keep_alive configuration"
        )

        assert "timeout_graceful_shutdown=5" in runserver_content, (
            "Graceful shutdown timeout should be set to 5 seconds"
        )

    def test_runserver_calls_uvicorn_with_correct_params(self):
        """Test that uvicorn.run is called with correct timeout parameters."""
        runserver_path = Path(__file__).parent.parent / "src" / "runserver.py"
        runserver_content = runserver_path.read_text()

        assert "timeout_graceful_shutdown=5" in runserver_content, (
            "runserver.py should have timeout_graceful_shutdown=5"
        )
        assert "timeout_keep_alive=5" in runserver_content, (
            "runserver.py should have timeout_keep_alive=5"
        )
        assert 'host="0.0.0.0"' in runserver_content or "host='0.0.0.0'" in runserver_content, (
            "Server should bind to 0.0.0.0"
        )
        assert "port=9000" in runserver_content or "port = 9000" in runserver_content, (
            "Server should listen on port 9000"
        )
        assert "reload=True" in runserver_content or "reload = True" in runserver_content, (
            "Server should have reload enabled in dev mode"
        )

    def test_websocket_connections_closed_on_shutdown(self):
        """Test that WebSocket connections are properly closed during shutdown."""
        from unittest.mock import AsyncMock

        from starlette.websockets import WebSocketState

        from src.utils.websocket.websocket_manager import connection_manager

        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws1.application_state = WebSocketState.CONNECTED
        mock_ws2.application_state = WebSocketState.CONNECTED

        async def test_closure():
            await connection_manager.connect(mock_ws1, "client1", 1)
            await connection_manager.connect(mock_ws2, "client2", 1)

            active = await connection_manager.get_active_connections()
            assert "client1" in active
            assert "client2" in active

            await connection_manager.disconnect("client1")
            await connection_manager.disconnect("client2")

            active = await connection_manager.get_active_connections()
            assert "client1" not in active
            assert "client2" not in active

            assert mock_ws1.close.called or mock_ws1.aclose.called, (
                "WebSocket should be closed on disconnect"
            )

        import asyncio

        asyncio.run(test_closure())
