"""
Test to verify event_listener sends full events data in correct format.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.football_events.db_services import FootballEventServiceDB
from src.utils.websocket.websocket_manager import MatchDataWebSocketManager


@pytest.mark.asyncio
class TestEventListenerFormat:
    """Test that event_listener sends events in correct format matching frontend expectations."""

    @pytest.fixture
    def mock_cache_service(self):
        cache_service = MagicMock()
        cache_service.invalidate_event_data = MagicMock()
        cache_service.invalidate_stats = MagicMock()
        return cache_service

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.get_session_maker = MagicMock()
        return db

    @pytest.fixture
    def mock_event_service(self):
        """Mock FootballEventServiceDB with sample events."""
        service = MagicMock(spec=FootballEventServiceDB)

        sample_events = [
            {
                "id": 1,
                "match_id": 100,
                "event_number": 1,
                "play_type": "run",
                "run_player": {
                    "id": 10,
                    "player_id": 5,
                    "player": {
                        "first_name": "John",
                        "second_name": "Doe",
                        "person_photo_url": "http://example.com/photo.jpg",
                    },
                    "position": {"id": 1, "name": "RB"},
                    "team": {"id": 1, "name": "Team A", "logo_url": "http://example.com/logo.png"},
                },
            }
        ]

        service.get_events_with_players = AsyncMock(return_value=sample_events)
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

    async def test_event_listener_sends_full_events_data_at_top_level(
        self, ws_manager, mock_connection, mock_event_service
    ):
        """
        Verify event_listener sends full events data at message top level.

        This is critical because frontend expects:
        message['events'] NOT message['data']['events']

        Reference: frontend-angular-signals/src/app/core/services/websocket.service.ts:540
        """
        import src.utils.websocket.websocket_manager as ws_module

        trigger_payload = json.dumps({"match_id": 100})
        mock_pid = 12345
        mock_channel = "football_event_change"

        with patch.object(FootballEventServiceDB, "__new__", return_value=mock_event_service):
            with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                mock_conn_mgr.send_to_all = AsyncMock()

                await ws_manager.event_listener(
                    mock_connection, mock_pid, mock_channel, trigger_payload
                )

                calls = mock_conn_mgr.send_to_all.call_args_list

                assert len(calls) == 2, "Should send both event-update and statistics-update"

                first_call_args = calls[0][0][0]
                assert first_call_args["type"] == "event-update"
                assert first_call_args["match_id"] == 100

                events = first_call_args.get("events")
                assert events is not None, "Events should be at top level of message"
                assert isinstance(events, list), "Events should be a list"
                assert len(events) == 1, "Should have 1 event"

                first_event = events[0]
                assert first_event["id"] == 1
                assert first_event["play_type"] == "run"
                assert "run_player" in first_event

    async def test_event_listener_handles_empty_events_list(self, ws_manager, mock_connection):
        """Verify event_listener sends empty list when no events exist."""
        import src.utils.websocket.websocket_manager as ws_module
        from src.football_events.db_services import FootballEventServiceDB

        trigger_payload = json.dumps({"match_id": 200})
        mock_pid = 12345
        mock_channel = "football_event_change"

        with patch.object(FootballEventServiceDB, "__new__") as mock_service_init:
            mock_event_service = MagicMock(spec=FootballEventServiceDB)
            mock_event_service.get_events_with_players = AsyncMock(return_value=[])
            mock_service_init.return_value = mock_event_service

            with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                mock_conn_mgr.send_to_all = AsyncMock()

                await ws_manager.event_listener(
                    mock_connection, mock_pid, mock_channel, trigger_payload
                )

                first_call_args = mock_conn_mgr.send_to_all.call_args_list[0][0][0]

                assert first_call_args["type"] == "event-update"
                assert first_call_args["match_id"] == 200
                assert first_call_args["events"] == []

    async def test_event_listener_invalidates_caches(
        self, ws_manager, mock_connection, mock_cache_service
    ):
        """Verify event_listener invalidates event_data and stats caches."""
        import src.utils.websocket.websocket_manager as ws_module
        from src.football_events.db_services import FootballEventServiceDB

        trigger_payload = json.dumps({"match_id": 300})

        with patch.object(FootballEventServiceDB, "__new__") as mock_service_init:
            mock_event_service = MagicMock(spec=FootballEventServiceDB)
            mock_event_service.get_events_with_players = AsyncMock(return_value=[])
            mock_service_init.return_value = mock_event_service

            with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                mock_conn_mgr.send_to_all = AsyncMock()

                await ws_manager.event_listener(
                    mock_connection, None, "football_event_change", trigger_payload
                )

                mock_cache_service.invalidate_event_data.assert_called_with(300)
                mock_cache_service.invalidate_stats.assert_called_with(300)

    async def test_event_listener_sends_statistics_update(
        self, ws_manager, mock_connection, mock_cache_service
    ):
        """Verify event_listener also sends statistics-update message."""
        import src.utils.websocket.websocket_manager as ws_module
        from src.football_events.db_services import FootballEventServiceDB

        trigger_payload = json.dumps({"match_id": 400})

        with patch.object(FootballEventServiceDB, "__new__") as mock_service_init:
            mock_event_service = MagicMock(spec=FootballEventServiceDB)
            mock_event_service.get_events_with_players = AsyncMock(return_value=[])
            mock_service_init.return_value = mock_event_service

            with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
                mock_conn_mgr.send_to_all = AsyncMock()

                await ws_manager.event_listener(
                    mock_connection, None, "football_event_change", trigger_payload
                )

                calls = mock_conn_mgr.send_to_all.call_args_list

                assert len(calls) == 2, (
                    "Should send two messages (event-update and statistics-update)"
                )

                first_call_args = calls[0][0][0]
                assert first_call_args["type"] == "event-update"

                second_call_args = calls[1][0][0]
                assert second_call_args["type"] == "statistics-update"

    async def test_gameclock_listener_sends_data_at_top_level(
        self, ws_manager, mock_connection, mock_cache_service
    ):
        """
        Verify gameclock_listener sends gameclock data at message top level.

        This is critical because frontend expects:
        message['gameclock'] NOT message['data']['gameclock']

        Reference: frontend-angular-signals/src/app/core/services/websocket.service.ts:356
        """
        import src.utils.websocket.websocket_manager as ws_module

        trigger_payload = json.dumps(
            {
                "table": "gameclock",
                "operation": "UPDATE",
                "match_id": 100,
                "data": {
                    "id": 1,
                    "match_id": 100,
                    "gameclock": 600,
                    "gameclock_time_remaining": 600,
                    "gameclock_max": 720,
                    "gameclock_status": "running",
                    "version": 1,
                },
            }
        )
        mock_pid = 12345
        mock_channel = "gameclock_change"

        with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
            mock_conn_mgr.send_to_all = AsyncMock()

            await ws_manager.gameclock_listener(
                mock_connection, mock_pid, mock_channel, trigger_payload
            )

            call_args = mock_conn_mgr.send_to_all.call_args[0][0]

            assert call_args["type"] == "gameclock-update"
            assert call_args["match_id"] == 100

            gameclock = call_args.get("gameclock")
            assert gameclock is not None, "Gameclock should be at top level of message"
            assert isinstance(gameclock, dict), "Gameclock should be a dict"
            assert gameclock["id"] == 1
            assert gameclock["gameclock"] == 600
            assert gameclock["gameclock_status"] == "running"
            assert "data" not in call_args, "Data should be moved to gameclock key"

    async def test_playclock_listener_sends_data_at_top_level(
        self, ws_manager, mock_connection, mock_cache_service
    ):
        """
        Verify playclock_listener sends playclock data at message top level.

        This is critical because frontend expects:
        message['playclock'] NOT message['data']['playclock']

        Reference: frontend-angular-signals/src/app/core/services/websocket.service.ts:333
        """
        import src.utils.websocket.websocket_manager as ws_module

        trigger_payload = json.dumps(
            {
                "table": "playclock",
                "operation": "UPDATE",
                "match_id": 200,
                "data": {
                    "id": 2,
                    "match_id": 200,
                    "playclock": 25,
                    "playclock_status": "running",
                    "version": 1,
                },
            }
        )
        mock_pid = 12345
        mock_channel = "playclock_change"

        with patch.object(ws_module, "connection_manager") as mock_conn_mgr:
            mock_conn_mgr.send_to_all = AsyncMock()

            await ws_manager.playclock_listener(
                mock_connection, mock_pid, mock_channel, trigger_payload
            )

            call_args = mock_conn_mgr.send_to_all.call_args[0][0]

            assert call_args["type"] == "playclock-update"
            assert call_args["match_id"] == 200

            playclock = call_args.get("playclock")
            assert playclock is not None, "Playclock should be at top level of message"
            assert isinstance(playclock, dict), "Playclock should be a dict"
            assert playclock["id"] == 2
            assert playclock["playclock"] == 25
            assert playclock["playclock_status"] == "running"
            assert "data" not in call_args, "Data should be moved to playclock key"
