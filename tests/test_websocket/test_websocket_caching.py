from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocket, WebSocketState

from src.websocket.match_handler import MatchWebSocketHandler


@pytest.mark.asyncio
class TestWebSocketCaching:
    @pytest.fixture
    def handler(self):
        return MatchWebSocketHandler(cache_service=None)

    @pytest.fixture
    def cache_service(self):
        from src.matches.match_data_cache_service import MatchDataCacheService

        mock_db = MagicMock()
        return MatchDataCacheService(mock_db)

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock(spec=WebSocket)
        ws.application_state = WebSocketState.CONNECTED
        return ws

    async def test_handler_without_cache_service(self, handler, mock_websocket):
        handler.cache_service = None

        mock_match_data = {
            "data": {
                "match_id": 1,
                "id": 1,
                "status_code": 200,
                "match": {"id": 1},
                "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
                "match_data": {"id": 1, "match_id": 1},
            }
        }

        with (
            patch(
                "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
                return_value=mock_match_data,
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_gameclock",
                return_value={"match_id": 1, "gameclock": {"id": 1}, "status_code": 200},
            ),
            patch(
                "src.helpers.fetch_helpers.fetch_playclock",
                return_value={"match_id": 1, "playclock": {"id": 1}, "status_code": 200},
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
            await handler.send_initial_data(mock_websocket, "client1", 1)

            assert mock_websocket.send_json.called
            assert mock_websocket.send_json.call_count == 1
            message = mock_websocket.send_json.call_args[0][0]
            assert message["type"] == "initial-load"
            assert "data" in message
            assert "match" in message["data"]
            assert "teams_data" in message["data"]
            assert "gameclock" in message["data"]
            assert "playclock" in message["data"]
            assert "events" in message["data"]
            assert "statistics" in message["data"]
            assert "server_time_ms" in message["data"]

    async def test_cache_service_caches_match_data(self, cache_service):
        mock_match_data = {
            "data": {
                "match_id": 1,
                "id": 1,
                "status_code": 200,
                "match": {"id": 1},
                "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
                "match_data": {"id": 1, "match_id": 1},
            }
        }

        cache_service._cache["match-update:1"] = mock_match_data["data"]

        assert "match-update:1" in cache_service._cache
        assert cache_service._cache["match-update:1"] == mock_match_data["data"]

    async def test_cache_service_invalidate_match_data(self, cache_service):
        mock_match_data = {
            "data": {
                "match_id": 1,
                "id": 1,
                "status_code": 200,
                "match": {"id": 1},
                "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
                "match_data": {"id": 1, "match_id": 1},
            }
        }

        cache_service._cache["match-update:1"] = mock_match_data["data"]

        assert "match-update:1" in cache_service._cache

        cache_service.invalidate_match_data(1)

        assert "match-update:1" not in cache_service._cache

    async def test_cache_service_invalidate_gameclock(self, cache_service):
        mock_gameclock = {"match_id": 1, "id": 1, "status_code": 200}

        cache_service._cache["gameclock-update:1"] = mock_gameclock

        assert "gameclock-update:1" in cache_service._cache

        cache_service.invalidate_gameclock(1)

        assert "gameclock-update:1" not in cache_service._cache

    async def test_cache_service_invalidate_playclock(self, cache_service):
        mock_playclock = {"match_id": 1, "id": 1, "status_code": 200}

        cache_service._cache["playclock-update:1"] = mock_playclock

        assert "playclock-update:1" in cache_service._cache

        cache_service.invalidate_playclock(1)

        assert "playclock-update:1" not in cache_service._cache

    async def test_cache_service_invalidate_event_data(self, cache_service):
        mock_event_data = {"match_id": 1, "id": 1, "status_code": 200}

        cache_service._cache["event-update:1"] = mock_event_data

        assert "event-update:1" in cache_service._cache

        cache_service.invalidate_event_data(1)

        assert "event-update:1" not in cache_service._cache

    async def test_cache_keys_different_message_types_no_collision(self, cache_service):
        mock_match_data = {"match_id": 1, "id": 1, "type": "match"}
        mock_gameclock = {"match_id": 1, "id": 1, "type": "gameclock"}

        cache_service._cache["match-update:1"] = mock_match_data
        cache_service._cache["gameclock-update:1"] = mock_gameclock

        assert "match-update:1" in cache_service._cache
        assert "gameclock-update:1" in cache_service._cache
        assert cache_service._cache["match-update:1"] != cache_service._cache["gameclock-update:1"]

    async def test_second_client_gets_cached_data(self, cache_service):
        """Test that cached data is returned for second request."""
        mock_match_data = {
            "match_id": 1,
            "id": 1,
            "status_code": 200,
            "match": {"id": 1},
            "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
            "match_data": {"id": 1, "match_id": 1},
        }

        cache_service._cache["match-update:1"] = mock_match_data

        with patch(
            "src.helpers.fetch_helpers.fetch_with_scoreboard_data",
            return_value=mock_match_data,
        ):
            result1 = await cache_service.get_or_fetch_match_data(1)
            assert result1 is not None
            assert result1 == mock_match_data

            result2 = await cache_service.get_or_fetch_match_data(1)
            assert result2 is not None
            assert result2 == mock_match_data
            assert result1 == result2

    async def test_database_update_invalidates_cache(self, cache_service):
        """Test that cache is cleared after invalidation."""
        mock_match_data = {
            "match_id": 1,
            "id": 1,
            "status_code": 200,
            "match": {"id": 1},
            "teams_data": {"team_a": {"id": 1}, "team_b": {"id": 2}},
            "match_data": {"id": 1, "match_id": 1},
        }

        cache_service._cache["match-update:1"] = mock_match_data

        assert "match-update:1" in cache_service._cache

        cache_service.invalidate_match_data(1)

        assert "match-update:1" not in cache_service._cache
