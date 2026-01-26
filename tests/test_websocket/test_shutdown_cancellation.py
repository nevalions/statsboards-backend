import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocket, WebSocketState

from src.websocket.match_handler import MatchWebSocketHandler


@pytest.mark.asyncio
class TestWebSocketShutdown:
    """Test WebSocket shutdown and cancellation handling."""

    @pytest.fixture
    def handler(self):
        return MatchWebSocketHandler(cache_service=None)

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock(spec=WebSocket)
        ws.application_state = WebSocketState.CONNECTED
        return ws

    async def test_cleanup_websocket_handles_cancellation(self, handler):
        """Test that cleanup_websocket handles CancelledError gracefully."""
        with (
            patch("src.utils.websocket.websocket_manager.connection_manager") as mock_cm,
            patch("src.utils.websocket.websocket_manager.ws_manager") as mock_ws,
        ):
            mock_cm.disconnect = AsyncMock()
            mock_ws.disconnect = AsyncMock()
            mock_ws.shutdown = AsyncMock()

            # Create a task that will be cancelled
            async def cancel_during_sleep():
                await handler.cleanup_websocket("test_client_id")

            task = asyncio.create_task(cancel_during_sleep())
            # Cancel task
            await asyncio.sleep(0.01)
            task.cancel()

            # Should not raise an unhandled exception
            try:
                await task
            except asyncio.CancelledError:
                # This is expected when a task is cancelled
                pass

    async def test_handle_websocket_connection_handles_cancellation(self, handler, mock_websocket):
        """Test that handle_websocket_connection handles CancelledError gracefully."""
        client_id = "test_client"
        match_id = 1

        mock_match_data = {
            "match_id": 1,
            "id": 1,
            "status_code": 200,
            "match": {"id": 1},
            "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
            "match_data": {"id": 1, "match_id": 1},
        }

        with (
            patch("src.utils.websocket.websocket_manager.connection_manager") as mock_cm,
            patch("src.utils.websocket.websocket_manager.ws_manager") as mock_ws,
            patch(
                "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
                return_value=mock_match_data,
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_gameclock",
                return_value={"match_id": 1, "id": 1, "status_code": 200},
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_playclock",
                return_value={"match_id": 1, "id": 1, "status_code": 200},
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_event",
                return_value={"match_id": 1, "id": 1, "status_code": 200, "events": []},
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_stats",
                return_value={"match_id": 1, "statistics": {}},
            ),
        ):
            mock_cm.connect = AsyncMock()
            mock_cm.disconnect = AsyncMock()
            mock_ws.startup = AsyncMock()
            mock_ws.disconnect = AsyncMock()
            mock_ws.shutdown = AsyncMock()

            # Mock queue to hang
            async def get_queue():
                async def get_data():
                    await asyncio.sleep(10)
                    return {"type": "test"}

                queue = MagicMock()
                queue.get = get_data
                return queue

            mock_cm.get_queue_for_client = get_queue

            # Create a connection task
            connection_task = asyncio.create_task(
                handler.handle_websocket_connection(mock_websocket, client_id, match_id)
            )

            # Give it time to start, then cancel (simulating shutdown)
            await asyncio.sleep(0.05)
            connection_task.cancel()

            # Should handle CancelledError gracefully
            try:
                await connection_task
            except asyncio.CancelledError:
                pass

    async def test_process_data_websocket_handles_cancellation(self, handler, mock_websocket):
        """Test that process_data_websocket handles CancelledError gracefully."""
        client_id = "test_client"
        match_id = 1

        with patch("src.utils.websocket.websocket_manager.connection_manager") as mock_cm:
            # Mock queue that will be cancelled
            async def get_queue():
                async def get_data():
                    await asyncio.sleep(10)
                    return {"type": "test"}

                queue = MagicMock()
                queue.get = get_data
                return queue

            mock_cm.get_queue_for_client = get_queue

            # Start processing task
            processing_task = asyncio.create_task(
                handler.process_data_websocket(mock_websocket, client_id, match_id)
            )

            # Give it time to start, then cancel (simulating shutdown)
            await asyncio.sleep(0.01)
            processing_task.cancel()

            # Should handle CancelledError gracefully
            try:
                await processing_task
            except asyncio.CancelledError:
                pass
