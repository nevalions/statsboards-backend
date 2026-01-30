"""
Test to verify players_update_listener sends players in correct format.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.matches.db_services import MatchServiceDB
from src.utils.websocket.websocket_manager import MatchDataWebSocketManager


@pytest.fixture
def mock_db():
    """Mock database for patching."""
    db = MagicMock()
    db.get_session_maker = MagicMock()
    return db


@pytest.mark.asyncio
class TestPlayersUpdateListenerFormat:
    """Test that players_update_listener sends players in correct format matching frontend expectations."""

    @pytest.fixture
    def mock_cache_service(self):
        cache_service = MagicMock()
        cache_service.invalidate_players = MagicMock()
        return cache_service

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.get_session_maker = MagicMock()
        return db

    @pytest.fixture
    def mock_match_service(self):
        """Mock MatchServiceDB with sample players."""
        service = MagicMock(spec=MatchServiceDB)

        sample_players = [
            {
                "id": 1,
                "player_id": 10,
                "player": {"id": 10, "first_name": "John", "second_name": "Doe"},
                "team": {"id": 1, "name": "Team A"},
                "position": {"id": 1, "name": "RB"},
                "player_team_tournament": {"id": 100},
                "person": {"id": 20, "first_name": "John", "second_name": "Doe"},
                "is_starting": True,
                "starting_type": "starter",
            }
        ]

        service.get_players_with_full_data_optimized = AsyncMock(return_value=sample_players)
        return service

    @pytest.fixture
    def ws_manager(self, mock_cache_service):
        """WebSocket manager with mock cache service."""
        manager = MatchDataWebSocketManager(db_url="postgresql://test")
        manager.set_cache_service(cache_service=mock_cache_service)
        return manager

    @pytest.fixture
    def mock_connection(self):
        """Mock PostgreSQL connection."""
        connection = MagicMock()
        return connection

    async def test_players_update_listener_sends_serialized_players(
        self, ws_manager, mock_connection, mock_match_service, mock_cache_service, mock_db
    ):
        """
        Verify players_update_listener serializes players data correctly.

        This is critical because:
        1. DB objects must be converted to dicts for JSON serialization
        2. Frontend expects: message['data']['players']
        3. Each player dict must be fully serializable (no DB objects)

        Reference: frontend-angular-signals/src/app/core/services/websocket.service.ts:811
        """
        import src.utils.websocket.websocket_manager as ws_module

        trigger_payload = json.dumps({"match_id": 100})
        mock_pid = 12345
        mock_channel = "player_match_change"

        with patch("src.core.db", mock_db):
            with patch.object(MatchServiceDB, "__new__", return_value=mock_match_service):
                with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                    mock_conn_mgr.send_to_all = AsyncMock()

                    await ws_manager.players_update_listener(
                        mock_connection, mock_pid, mock_channel, trigger_payload
                    )

                    calls = mock_conn_mgr.send_to_all.call_args_list
                    assert len(calls) == 1, "Should send one players-update message"

                    message = calls[0].kwargs.get("message") or calls[0][0][0]
                    assert message["type"] == "players-update"
                    assert "data" in message
                    assert message["data"]["match_id"] == 100
                    assert "players" in message["data"]

                    players = message["data"]["players"]
                    assert len(players) == 1

                    player = players[0]
                    assert player["id"] == 1
                    assert player["player_id"] == 10
                    assert player["player"]["id"] == 10
                    assert player["team"]["id"] == 1
                    assert player["position"]["id"] == 1
                    assert player["is_starting"] is True

                    mock_cache_service.invalidate_players.assert_called_once_with(100)

    async def test_players_update_listener_handles_empty_players(
        self, ws_manager, mock_connection, mock_match_service, mock_cache_service, mock_db
    ):
        """Verify players_update_listener handles empty players list correctly."""
        import src.utils.websocket.websocket_manager as ws_module

        mock_match_service.get_players_with_full_data_optimized = AsyncMock(return_value=[])
        trigger_payload = json.dumps({"match_id": 100})
        mock_pid = 12345
        mock_channel = "player_match_change"

        with patch("src.core.db", mock_db):
            with patch.object(MatchServiceDB, "__new__", return_value=mock_match_service):
                with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                    mock_conn_mgr.send_to_all = AsyncMock()

                    await ws_manager.players_update_listener(
                        mock_connection, mock_pid, mock_channel, trigger_payload
                    )

                    call = mock_conn_mgr.send_to_all.call_args
                    message = call.kwargs.get("message") or call[0][0]

                    assert message["type"] == "players-update"
                    assert message["data"]["players"] == []
