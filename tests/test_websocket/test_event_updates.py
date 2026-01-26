from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocket, WebSocketState

from src.matches.match_data_cache_service import MatchDataCacheService
from src.utils.websocket.websocket_manager import MatchDataWebSocketManager
from src.websocket.match_handler import MatchWebSocketHandler


@pytest.mark.asyncio
class TestEventUpdates:
    @pytest.fixture
    def cache_service(self):
        mock_db = MagicMock()
        return MatchDataCacheService(mock_db)

    @pytest.fixture
    def ws_manager(self):
        manager = MatchDataWebSocketManager(db_url="postgresql://test")
        manager.set_cache_service(cache_service=self.cache_service)
        return manager

    async def test_event_listener_invalidates_event_cache(self, cache_service, ws_manager):
        mock_event_data = {"match_id": 1, "id": 1, "status_code": 200}

        cache_service._cache["event-update:1"] = mock_event_data

        assert "event-update:1" in cache_service._cache

        ws_manager.invalidate_event_data = AsyncMock()
        await ws_manager.invalidate_event_data(1)

        assert ws_manager.invalidate_event_data.called

    async def test_event_listener_invalidates_match_cache(self, cache_service):
        mock_match_data = {"match_id": 1, "id": 1, "status_code": 200}

        cache_service._cache["match-update:1"] = mock_match_data

        assert "match-update:1" in cache_service._cache

        cache_service.invalidate_match_data(1)

        assert "match-update:1" not in cache_service._cache

    async def test_event_data_caching(self, cache_service):
        mock_event_data = {"match_id": 1, "id": 1, "events": []}

        cache_service._cache["event-update:1"] = mock_event_data

        assert "event-update:1" in cache_service._cache

        cache_service.invalidate_event_data(1)

        assert "event-update:1" not in cache_service._cache

    async def test_different_cache_types_dont_collide(self, cache_service):
        mock_match_data = {"match_id": 1, "id": 1}
        mock_event_data = {"match_id": 1, "id": 1}

        cache_service._cache["match-update:1"] = mock_match_data
        cache_service._cache["event-update:1"] = mock_event_data

        assert "match-update:1" in cache_service._cache
        assert "event-update:1" in cache_service._cache

        cache_service.invalidate_match_data(1)
        cache_service.invalidate_event_data(1)

        assert "match-update:1" not in cache_service._cache
        assert "event-update:1" not in cache_service._cache

    async def test_gameclock_invalidation_doesnt_affect_match_cache(self, cache_service):
        mock_match_data = {"match_id": 1, "id": 1}
        mock_gameclock = {"match_id": 1, "id": 1}

        cache_service._cache["match-update:1"] = mock_match_data
        cache_service._cache["gameclock-update:1"] = mock_gameclock

        cache_service.invalidate_gameclock(1)

        assert "match-update:1" in cache_service._cache
        assert "gameclock-update:1" not in cache_service._cache

    async def test_event_insert_invalidates_event_cache(self, cache_service):
        mock_event_data = {
            "match_id": 1,
            "id": 1,
            "events": [
                {
                    "id": 1,
                    "play_type": "run",
                    "event_number": 1,
                    "run_player": {"id": 10, "first_name": "John", "last_name": "Doe"},
                }
            ],
        }

        cache_service._cache["event-update:1"] = mock_event_data

        assert "event-update:1" in cache_service._cache

        cache_service.invalidate_event_data(1)

        assert "event-update:1" not in cache_service._cache

    async def test_event_update_invalidates_match_cache(self, cache_service):
        mock_match_data = {"match_id": 1, "id": 1, "match": {"id": 1}}
        mock_event_data = {"match_id": 1, "id": 1, "events": []}

        cache_service._cache["match-update:1"] = mock_match_data
        cache_service._cache["event-update:1"] = mock_event_data

        assert "match-update:1" in cache_service._cache

        cache_service.invalidate_event_data(1)

        assert "event-update:1" not in cache_service._cache

    async def test_event_update_invalidates_stats_cache(self, cache_service):
        mock_stats_data = {"match_id": 1, "id": 1, "stats": {"team_a": {}, "team_b": {}}}
        mock_event_data = {"match_id": 1, "id": 1, "events": []}

        cache_service._cache["stats-update:1"] = mock_stats_data
        cache_service._cache["event-update:1"] = mock_event_data

        assert "stats-update:1" in cache_service._cache

        cache_service.invalidate_event_data(1)

        assert "event-update:1" not in cache_service._cache

    async def test_event_data_includes_player_relationships(self, cache_service):
        mock_event_data = {
            "match_id": 1,
            "id": 1,
            "events": [
                {
                    "id": 1,
                    "play_type": "run",
                    "event_number": 1,
                    "run_player": {
                        "id": 10,
                        "first_name": "John",
                        "last_name": "Doe",
                        "player_number": "25",
                    },
                    "pass_received_player": {
                        "id": 15,
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "player_number": "88",
                    },
                }
            ],
        }

        cache_service._cache["event-update:1"] = mock_event_data

        assert "event-update:1" in cache_service._cache

        events = cache_service._cache["event-update:1"]["events"]
        assert len(events) == 1
        assert "run_player" in events[0]
        assert events[0]["run_player"]["id"] == 10
        assert events[0]["run_player"]["first_name"] == "John"
        assert "pass_received_player" in events[0]


@pytest.mark.asyncio
class TestWebSocketEventUpdateHandler:
    @pytest.fixture
    def handler(self):
        return MatchWebSocketHandler(cache_service=None)

    @pytest.fixture
    def cache_service(self):
        mock_db = MagicMock()
        return MatchDataCacheService(mock_db)

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock(spec=WebSocket)
        ws.application_state = WebSocketState.CONNECTED
        return ws

    async def test_process_event_data_sends_to_websocket(self, handler, mock_websocket):
        mock_event_data = {
            "match_id": 1,
            "id": 1,
            "status_code": 200,
            "events": [
                {
                    "id": 1,
                    "play_type": "run",
                    "event_number": 1,
                }
            ],
        }

        with patch(
            "src.helpers.fetch_helpers.fetch_event",
            return_value=mock_event_data,
        ):
            await handler.process_event_data(mock_websocket, 1)

            assert mock_websocket.send_json.called
            sent_data = mock_websocket.send_json.call_args[0][0]
            assert sent_data["type"] == "event-update"
            assert sent_data["match_id"] == 1
            assert "events" in sent_data

    async def test_process_event_data_with_provided_data(self, handler, mock_websocket):
        provided_data = {
            "match_id": 1,
            "id": 1,
            "type": "event-update",
            "events": [{"id": 1, "play_type": "pass"}],
        }

        await handler.process_event_data(mock_websocket, 1, provided_data)

        assert mock_websocket.send_json.called
        sent_data = mock_websocket.send_json.call_args[0][0]
        assert sent_data["type"] == "event-update"
        assert sent_data == provided_data

    async def test_process_event_data_websocket_disconnected(self, handler, mock_websocket):
        mock_websocket.application_state = WebSocketState.DISCONNECTED

        await handler.process_event_data(mock_websocket, 1)

        assert not mock_websocket.send_json.called

    async def test_process_event_data_connection_error_handling(
        self, handler, cache_service, mock_websocket
    ):
        mock_websocket.send_json.side_effect = Exception("Connection closed")

        handler.cache_service = cache_service

        mock_event_data = {"match_id": 1, "id": 1, "events": []}

        with patch(
            "src.helpers.fetch_helpers.fetch_event",
            return_value=mock_event_data,
        ):
            await handler.process_event_data(mock_websocket, 1)

            assert mock_websocket.send_json.called
