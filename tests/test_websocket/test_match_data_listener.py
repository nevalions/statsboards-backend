import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.websocket.websocket_manager import MatchDataWebSocketManager


@pytest.mark.asyncio
class TestMatchDataListener:
    async def test_match_data_listener_uses_trigger_data_when_available(self):
        manager = MatchDataWebSocketManager(db_url="postgresql://test")
        manager._cache_service = MagicMock()
        manager._cache_service.invalidate_match_data = MagicMock()
        manager.logger = MagicMock()

        payload = json.dumps({"match_id": 67, "data": {"score_team_a": 22, "score_team_b": 40}})

        mock_connection = MagicMock()

        with patch("src.utils.websocket.websocket_manager.connection_manager") as mock_conn_mgr:
            with patch(
                "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
                new_callable=AsyncMock,
            ) as mock_fetch:
                mock_conn_mgr.send_to_all = AsyncMock()

                await manager.match_data_listener(
                    mock_connection, None, "matchdata_change", payload
                )

                mock_conn_mgr.send_to_all.assert_called_once()
                mock_fetch.assert_not_called()

                call_args = mock_conn_mgr.send_to_all.call_args
                message_sent = call_args[0][0]

                assert message_sent["type"] == "match-update"
                assert "data" in message_sent
                assert message_sent["data"]["score_team_a"] == 22
                assert message_sent["data"]["score_team_b"] == 40

                manager._cache_service.invalidate_match_data.assert_called_once_with(67)

    async def test_match_data_listener_falls_back_to_full_fetch_when_no_trigger_data(self):
        manager = MatchDataWebSocketManager(db_url="postgresql://test")
        manager._cache_service = MagicMock()
        manager._cache_service.invalidate_match_data = MagicMock()
        manager.logger = MagicMock()

        payload = json.dumps({"match_id": 67})

        mock_connection = MagicMock()
        mock_full_data = {
            "data": {
                "match_id": 67,
                "id": 67,
                "match": {"id": 67, "team_a_id": 1, "team_b_id": 2},
                "teams_data": {
                    "team_a": {"id": 1, "title": "Team A"},
                    "team_b": {"id": 2, "title": "Team B"},
                },
                "match_data": {"score_team_a": 22, "score_team_b": 40},
                "scoreboard_data": {"is_main_sponsor": False},
                "players": [],
                "events": [],
            }
        }

        with patch("src.utils.websocket.websocket_manager.connection_manager") as mock_conn_mgr:
            with patch(
                "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
                new_callable=AsyncMock,
            ) as mock_fetch:
                mock_fetch.return_value = mock_full_data
                mock_conn_mgr.send_to_all = AsyncMock()

                await manager.match_data_listener(
                    mock_connection, None, "matchdata_change", payload
                )

                mock_conn_mgr.send_to_all.assert_called_once()
                mock_fetch.assert_called_once()

                call_args = mock_conn_mgr.send_to_all.call_args
                message_sent = call_args[0][0]

                assert message_sent["type"] == "match-update"
                assert "data" in message_sent
                assert message_sent["data"]["match_id"] == 67
                assert message_sent["data"]["match_data"]["score_team_a"] == 22
                assert message_sent["data"]["teams_data"]["team_a"]["title"] == "Team A"

                manager._cache_service.invalidate_match_data.assert_called_once_with(67)

    async def test_match_data_listener_handles_fetch_failure_when_no_trigger_data(self):
        manager = MatchDataWebSocketManager(db_url="postgresql://test")
        manager._cache_service = None
        manager.logger = MagicMock()

        payload = json.dumps({"match_id": 67})

        mock_connection = MagicMock()

        with patch("src.utils.websocket.websocket_manager.connection_manager") as mock_conn_mgr:
            with patch(
                "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
                new_callable=AsyncMock,
            ) as mock_fetch:
                mock_fetch.return_value = None
                mock_conn_mgr.send_to_all = AsyncMock()

                await manager.match_data_listener(
                    mock_connection, None, "matchdata_change", payload
                )

                mock_conn_mgr.send_to_all.assert_called_once()

                call_args = mock_conn_mgr.send_to_all.call_args
                message_sent = call_args[0][0]

                assert message_sent["type"] == "match-update"
                assert "data" in message_sent
                # When fetch fails and no trigger data, send empty dict
                assert message_sent["data"] == {}
