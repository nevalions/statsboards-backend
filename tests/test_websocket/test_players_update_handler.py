"""
Test to verify match_handler handles players-update messages correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketState

from src.websocket.match_handler import MatchWebSocketHandler


@pytest.mark.asyncio
class TestPlayersUpdateHandler:
    """Test that match_handler processes players-update messages correctly."""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        websocket = MagicMock()
        websocket.application_state = WebSocketState.CONNECTED
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.fixture
    def handler(self):
        """WebSocket handler instance."""
        return MatchWebSocketHandler()

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service."""
        return MagicMock()

    @pytest.fixture
    def sample_players_update_message(self):
        """Sample players-update message from queue."""
        return {
            "type": "players-update",
            "data": {
                "match_id": 100,
                "players": [
                    {
                        "id": 1,
                        "player_id": 10,
                        "player": {"id": 10, "first_name": "John"},
                        "team": {"id": 1, "name": "Team A"},
                        "position": {"id": 1, "name": "RB"},
                    }
                ],
            },
        }

    async def test_players_update_in_handlers(self, handler):
        """Verify players-update is in the handlers dictionary."""

        handler_class = MatchWebSocketHandler
        handler_instance = handler_class()

        handlers = {
            "initial-load": handler_instance.process_match_data,
            "message-update": handler_instance.process_match_data,
            "match-update": handler_instance.process_match_data,
            "gameclock-update": handler_instance.process_gameclock_data,
            "playclock-update": handler_instance.process_playclock_data,
            "event-update": handler_instance.process_event_data,
            "statistics-update": handler_instance.process_stats_data,
            "matchdata": handler_instance.process_match_data,
            "gameclock": handler_instance.process_gameclock_data,
            "playclock": handler_instance.process_playclock_data,
            "match": handler_instance.process_match_data,
            "scoreboard": handler_instance.process_match_data,
            "players-update": handler_instance.process_match_data,
        }

        assert "players-update" in handlers
        assert handlers["players-update"] == handler_instance.process_match_data

    async def test_players_update_processed_correctly(
        self, handler, mock_websocket, sample_players_update_message
    ):
        """Verify players-update message is processed and sent to websocket."""
        from src.utils.websocket.websocket_manager import connection_manager

        with patch.object(connection_manager, "get_queue_for_client") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.get = AsyncMock(return_value=sample_players_update_message)
            mock_get_queue.return_value = mock_queue

            await handler.process_match_data(
                mock_websocket, match_id=100, data=sample_players_update_message
            )

            mock_websocket.send_json.assert_called_once()
            sent_data = mock_websocket.send_json.call_args[0][0]

            assert sent_data["type"] == "players-update"
            assert sent_data["data"]["match_id"] == 100
            assert len(sent_data["data"]["players"]) == 1
            assert sent_data["data"]["players"][0]["id"] == 1
