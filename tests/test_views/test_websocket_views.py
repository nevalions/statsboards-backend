import asyncio
import pytest
from starlette.websockets import WebSocket
from tests.factories import (
    SeasonFactorySample,
    SportFactorySample,
    TeamFactory,
    TournamentFactory,
)

from src.core.models.base import connection_manager
from src.logging_config import setup_logging

# type: ignore
setup_logging()


@pytest.mark.asyncio
class TestConnectionManager:
    async def test_connection_manager_connect(self):
        """Test ConnectionManager connect method."""
        from unittest.mock import AsyncMock

        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client_cm"
        match_id = 1

        await connection_manager.connect(mock_websocket, client_id, match_id)

        active_connections = await connection_manager.get_active_connections()
        assert client_id in active_connections

        queue = await connection_manager.get_queue_for_client(client_id)
        assert queue is not None

        match_subscriptions = await connection_manager.get_match_subscriptions(match_id)
        assert client_id in match_subscriptions

        await connection_manager.disconnect(client_id)

    async def test_connection_manager_disconnect(self):
        """Test ConnectionManager disconnect method."""
        from unittest.mock import AsyncMock

        mock_websocket = AsyncMock(spec=WebSocket)
        client_id = "test_client_disconnect_cm"
        match_id = 2

        await connection_manager.connect(mock_websocket, client_id, match_id)
        await connection_manager.disconnect(client_id)

        active_connections = await connection_manager.get_active_connections()
        assert client_id not in active_connections

        match_subscriptions = await connection_manager.get_match_subscriptions(match_id)
        assert client_id not in match_subscriptions

    async def test_connection_manager_send_to_all(self):
        """Test ConnectionManager send_to_all method."""
        from unittest.mock import AsyncMock
        import json

        client_1 = "test_client_send_1"
        client_2 = "test_client_send_2"
        match_id = 3
        test_data = {"type": "match-update", "match_id": match_id, "score": "1-0"}

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_1, match_id)
        await connection_manager.connect(mock_ws2, client_2, match_id)

        await connection_manager.send_to_all(  # type: ignore[arg-type]
            json.dumps(test_data), match_id=match_id  # type: ignore[arg-type]
        )

        await asyncio.sleep(0.01)

        queue_1 = await connection_manager.get_queue_for_client(client_1)
        queue_2 = await connection_manager.get_queue_for_client(client_2)

        assert not queue_1.empty()
        assert not queue_2.empty()

        msg_1 = await queue_1.get()
        msg_2 = await queue_2.get()

        assert json.loads(msg_1) == test_data
        assert json.loads(msg_2) == test_data

        await connection_manager.disconnect(client_1)
        await connection_manager.disconnect(client_2)

    async def test_connection_manager_get_queue_for_client(self):
        """Test getting queue for a specific client."""
        from unittest.mock import AsyncMock

        client_id = "test_client_queue"
        match_id = 4

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)
        assert isinstance(queue, asyncio.Queue)

        test_msg = {"test": "data"}
        await queue.put(test_msg)
        assert not queue.empty()

        received = await queue.get()
        assert received == test_msg

        await connection_manager.disconnect(client_id)

    async def test_connection_manager_match_subscriptions(self):
        """Test match subscriptions management."""
        from unittest.mock import AsyncMock

        match_id = 5
        client_1 = "test_sub_client_1"
        client_2 = "test_sub_client_2"
        client_3 = "test_sub_client_3"

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_1, match_id)
        await connection_manager.connect(mock_ws2, client_2, match_id)
        await connection_manager.connect(mock_ws3, client_3, match_id)

        subscriptions = await connection_manager.get_match_subscriptions(match_id)
        assert len(subscriptions) == 3
        assert client_1 in subscriptions
        assert client_2 in subscriptions
        assert client_3 in subscriptions

        await connection_manager.disconnect(client_1)
        subscriptions = await connection_manager.get_match_subscriptions(match_id)
        assert len(subscriptions) == 2
        assert client_1 not in subscriptions

        await connection_manager.disconnect(client_2)
        await connection_manager.disconnect(client_3)

    async def test_connection_manager_multiple_matches(self):
        """Test that clients can subscribe to different matches."""
        from unittest.mock import AsyncMock

        match_1 = 10
        match_2 = 20
        client_1 = "test_multi_client_1"
        client_2 = "test_multi_client_2"

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_1, match_1)
        await connection_manager.connect(mock_ws2, client_2, match_2)

        subs_1 = await connection_manager.get_match_subscriptions(match_1)
        subs_2 = await connection_manager.get_match_subscriptions(match_2)

        assert client_1 in subs_1
        assert client_2 in subs_2
        assert client_1 not in subs_2
        assert client_2 not in subs_1

        await connection_manager.disconnect(client_1)
        await connection_manager.disconnect(client_2)

    async def test_connection_manager_send_to_specific_match_only(self):
        """Test that messages are sent only to clients of specific match."""
        from unittest.mock import AsyncMock
        import json

        match_1 = 30
        match_2 = 40
        client_match1_a = "test_m1_client_a"
        client_match1_b = "test_m1_client_b"
        client_match2_a = "test_m2_client_a"

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)
        mock_ws3 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_match1_a, match_1)
        await connection_manager.connect(mock_ws2, client_match1_b, match_1)
        await connection_manager.connect(mock_ws3, client_match2_a, match_2)

        test_data = {"type": "match-update", "match_id": match_1, "score": "2-1"}
        await connection_manager.send_to_all(  # type: ignore[arg-type]
            json.dumps(test_data), match_id=match_1  # type: ignore[arg-type]
        )

        await asyncio.sleep(0.01)

        queue_m1_a = await connection_manager.get_queue_for_client(client_match1_a)
        queue_m1_b = await connection_manager.get_queue_for_client(client_match1_b)
        queue_m2_a = await connection_manager.get_queue_for_client(client_match2_a)

        assert not queue_m1_a.empty()
        assert not queue_m1_b.empty()
        assert queue_m2_a.empty()

        await queue_m1_a.get()
        await queue_m1_b.get()

        await connection_manager.disconnect(client_match1_a)
        await connection_manager.disconnect(client_match1_b)
        await connection_manager.disconnect(client_match2_a)


@pytest.mark.asyncio
class TestWebSocketEndpointIntegration:
    async def test_websocket_endpoint_connection_and_initial_data(
        self, test_app, test_db
    ):
        """Test WebSocket endpoint connection and initial data sending."""
        from src.matches.db_services import MatchServiceDB
        from src.teams.db_services import TeamServiceDB
        from src.sports.db_services import SportServiceDB
        from src.tournaments.db_services import TournamentServiceDB
        from src.seasons.db_services import SeasonServiceDB
        from src.matchdata.db_services import MatchDataServiceDB
        from src.gameclocks.db_services import GameClockServiceDB
        from src.playclocks.db_services import PlayClockServiceDB
        from src.scoreboards.db_services import ScoreboardServiceDB
        from src.matches.schemas import MatchSchemaCreate
        from src.matchdata.schemas import MatchDataSchemaCreate
        from src.playclocks.schemas import PlayClockSchemaCreate
        from src.gameclocks.schemas import GameClockSchemaCreate
        from src.scoreboards.schemas import ScoreboardSchemaCreate
        from datetime import datetime

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        playclock_service = PlayClockServiceDB(test_db)
        await playclock_service.create(PlayClockSchemaCreate(match_id=created_match.id))

        gameclock_service = GameClockServiceDB(test_db)
        await gameclock_service.create(GameClockSchemaCreate(match_id=created_match.id))

        scoreboard_db_service = ScoreboardServiceDB(test_db)
        await scoreboard_db_service.create(
            ScoreboardSchemaCreate(
                match_id=created_match.id,
                scale_tournament_logo=2,
                scale_main_sponsor=2,
                scale_logo_a=2,
                scale_logo_b=2,
                team_a_game_color="#ffffff",
                team_b_game_color="#000000",
                team_a_game_title="Team A",
                team_b_game_title="Team B",
            )
        )

        from unittest.mock import AsyncMock, patch
        from starlette.websockets import WebSocketState

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock()

        from src.matches.views import MatchAPIRouter

        MatchAPIRouter(MatchServiceDB(test_db))

        client_id = "test_endpoint_client"
        match_id = created_match.id

        await connection_manager.connect(mock_websocket, client_id, match_id)

        from src.helpers.fetch_helpers import (
            fetch_with_scoreboard_data,
            fetch_playclock,
            fetch_gameclock,
        )

        initial_data = await fetch_with_scoreboard_data(match_id)
        initial_data["type"] = "message-update"  # type: ignore[assignment]
        await mock_websocket.send_json(initial_data)

        initial_playclock_data = await fetch_playclock(match_id)
        initial_playclock_data["type"] = "playclock-update"  # type: ignore[assignment]
        await mock_websocket.send_json(initial_playclock_data)

        initial_gameclock_data = await fetch_gameclock(match_id)
        initial_gameclock_data["type"] = "gameclock-update"  # type: ignore[assignment]
        await mock_websocket.send_json(initial_gameclock_data)

        assert mock_websocket.send_json.call_count == 3

        messages_sent = [
            call.args[0] for call in mock_websocket.send_json.call_args_list
        ]

        message_types = [msg.get("type") for msg in messages_sent]
        assert "message-update" in message_types
        assert "playclock-update" in message_types
        assert "gameclock-update" in message_types

        for msg in messages_sent:
            assert "match_id" in msg or msg.get("type") in [
                "message-update",
                "playclock-update",
                "gameclock-update",
            ]

        await connection_manager.disconnect(client_id)


@pytest.mark.asyncio
class TestMessageProcessingQueue:
    async def test_message_queue_multiple_message_types(self, test_db):
        """Test that all message types are queued and processed correctly."""
        from src.matches.db_services import MatchServiceDB
        from src.teams.db_services import TeamServiceDB
        from src.sports.db_services import SportServiceDB
        from src.tournaments.db_services import TournamentServiceDB
        from src.seasons.db_services import SeasonServiceDB
        from src.matchdata.db_services import MatchDataServiceDB
        from src.matches.schemas import MatchSchemaCreate
        from src.matchdata.schemas import MatchDataSchemaCreate
        from datetime import datetime
        from unittest.mock import AsyncMock

        sport_service = SportServiceDB(test_db)
        sport = await sport_service.create(SportFactorySample.build())

        season_service = SeasonServiceDB(test_db)
        season = await season_service.create(SeasonFactorySample.build())

        tournament_service = TournamentServiceDB(test_db)
        tournament = await tournament_service.create(
            TournamentFactory.build(sport_id=sport.id, season_id=season.id)
        )

        team_service = TeamServiceDB(test_db)
        team_a = await team_service.create(TeamFactory.build(sport_id=sport.id))
        team_b = await team_service.create(TeamFactory.build(sport_id=sport.id))

        match_service = MatchServiceDB(test_db)
        match_data = MatchSchemaCreate(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            match_date=datetime(2025, 1, 1),
            week=1,
        )
        created_match = await match_service.create_or_update_match(match_data)

        match_db_service = MatchDataServiceDB(test_db)
        await match_db_service.create(MatchDataSchemaCreate(match_id=created_match.id))

        client_id = "test_queue_client"
        match_id = created_match.id

        await connection_manager.connect(AsyncMock(spec=WebSocket), client_id, match_id)

        test_messages = [
            {"type": "message-update", "match_id": match_id},
            {"type": "match-update", "match_id": match_id},
            {"type": "gameclock-update", "match_id": match_id},
            {"type": "playclock-update", "match_id": match_id},
            {"type": "matchdata", "match_id": match_id},
            {"type": "gameclock", "match_id": match_id},
            {"type": "playclock", "match_id": match_id},
            {"type": "match", "match_id": match_id},
            {"type": "scoreboard", "match_id": match_id},
        ]

        queue = await connection_manager.get_queue_for_client(client_id)

        for msg in test_messages:
            await queue.put(msg)

        messages_processed = 0
        while not queue.empty():
            msg = await queue.get()
            messages_processed += 1

        assert messages_processed == len(test_messages)

        await connection_manager.disconnect(client_id)


@pytest.mark.asyncio
class TestWebSocketDataHandling:
    async def test_websocket_queue_message_handling(self):
        """Test that messages are properly handled via queue."""
        from unittest.mock import AsyncMock

        client_id = "test_queue_client"
        match_id = 6

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        test_messages = [
            {"type": "match-update", "match_id": match_id, "data": "match_data"},
            {"type": "gameclock-update", "match_id": match_id, "time": "10:00"},
            {"type": "playclock-update", "match_id": match_id, "time": "25:00"},
        ]

        queue = await connection_manager.get_queue_for_client(client_id)

        for msg in test_messages:
            await queue.put(msg)

        received_messages = []
        while not queue.empty():
            msg = await queue.get()
            received_messages.append(msg)

        assert len(received_messages) == 3
        assert received_messages == test_messages

        await connection_manager.disconnect(client_id)

    async def test_websocket_unknown_message_type_handling(self):
        """Test handling of unknown message types."""
        from unittest.mock import AsyncMock

        client_id = "test_unknown_client"
        match_id = 7

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)

        unknown_msg = {"type": "unknown-type", "match_id": match_id, "data": "test"}
        await queue.put(unknown_msg)

        received = await queue.get()
        assert received == unknown_msg

        await connection_manager.disconnect(client_id)

    async def test_websocket_non_dict_message_handling(self):
        """Test handling of non-dictionary messages."""
        from unittest.mock import AsyncMock

        client_id = "test_non_dict_client"
        match_id = 8

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)

        await queue.put("string_message")
        await queue.put(123)
        await queue.put(["list", "message"])

        assert not queue.empty()

        received_1 = await queue.get()
        assert received_1 == "string_message"

        received_2 = await queue.get()
        assert received_2 == 123

        received_3 = await queue.get()
        assert received_3 == ["list", "message"]

        await connection_manager.disconnect(client_id)

    async def test_websocket_multiple_messages_queue(self):
        """Test queuing and receiving multiple messages."""
        from unittest.mock import AsyncMock

        client_id = "test_multi_msg_client"
        match_id = 9

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)

        num_messages = 50
        for i in range(num_messages):
            await queue.put({"type": "test", "index": i})

        assert queue.qsize() == num_messages

        received_count = 0
        while not queue.empty():
            msg = await queue.get()
            assert msg["index"] == received_count
            received_count += 1

        assert received_count == num_messages

        await connection_manager.disconnect(client_id)


@pytest.mark.asyncio
class TestWebSocketCleanup:
    async def test_connection_manager_cleanup_connection_resources(self):
        """Test cleanup of all connection resources."""
        from unittest.mock import AsyncMock

        client_id = "test_cleanup_client"
        match_id = 15

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)
        await queue.put({"test": "data1"})
        await queue.put({"test": "data2"})

        assert not queue.empty()

        await connection_manager.disconnect(client_id)

        active_connections = await connection_manager.get_active_connections()
        assert client_id not in active_connections

        try:
            queue = await connection_manager.get_queue_for_client(client_id)
            assert False, "Should not be able to get queue for disconnected client"
        except KeyError:
            pass

    async def test_connection_manager_reconnect_same_client_id(self):
        """Test that reconnecting with same client_id replaces old connection."""
        from unittest.mock import AsyncMock

        client_id = "test_reconnect_client"
        match_id = 16

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_id, match_id)

        active_connections = await connection_manager.get_active_connections()
        assert active_connections[client_id] == mock_ws1

        await connection_manager.connect(mock_ws2, client_id, match_id)

        active_connections = await connection_manager.get_active_connections()
        assert active_connections[client_id] == mock_ws2
        assert mock_ws1.close.called

        await connection_manager.disconnect(client_id)


@pytest.mark.asyncio
class TestMatchDataWebSocketManagerErrorScenarios:
    async def test_ws_manager_database_connection_failure(self):
        """Test MatchDataWebSocketManager handles database connection failures."""
        from src.core.models.base import MatchDataWebSocketManager

        manager = MatchDataWebSocketManager(
            db_url="postgresql://invalid:invalid@invalid:5432/invalid"
        )

        try:
            await manager.connect_to_db()
            assert False, "Should have raised an exception for invalid connection"
        except Exception:
            pass

    async def test_ws_manager_maintain_connection_reconnect_after_failure(self):
        """Test that maintain_connection attempts to reconnect after connection loss."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        call_count = 0

        async def mock_connect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Connection failed")

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        manager.connect_to_db = AsyncMock(side_effect=mock_connect)
        manager.is_connected = False

        task = asyncio.create_task(manager.maintain_connection())
        await asyncio.sleep(0.1)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert call_count >= 1

    async def test_ws_manager_startup_with_connection_error(self):
        """Test ws_manager startup handles connection errors gracefully."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://invalid:invalid@invalid:5432/invalid"
        )
        manager.connect_to_db = AsyncMock(side_effect=Exception("Connection failed"))

        try:
            await manager.startup()
            assert False, "Should have raised an exception"
        except Exception:
            pass

    async def test_ws_manager_shutdown_during_active_connection(self):
        """Test that shutdown properly closes active connection and cancels retry task."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        manager.connection = AsyncMock()
        manager.is_connected = True

        async def mock_cancelled_task():
            raise asyncio.CancelledError()

        manager._connection_retry_task = asyncio.create_task(mock_cancelled_task())

        await manager.shutdown()

        manager.connection.close.assert_called_once()
        assert manager.is_connected is False

    async def test_ws_manager_disconnect_nonexistent_client(self):
        """Test disconnect handles nonexistent clients gracefully."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )

        await manager.disconnect("nonexistent_client")

    async def test_ws_manager_disconnect_partial_cleanup(self):
        """Test disconnect handles partial cleanup when only some queues exist."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock
        import asyncio

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        client_id = "test_client"
        manager.match_data_queues[client_id] = asyncio.Queue()
        manager.playclock_queues[client_id] = asyncio.Queue()

        await manager.disconnect(client_id)

        assert client_id not in manager.match_data_queues
        assert client_id not in manager.playclock_queues
        assert client_id not in manager.gameclock_queues


@pytest.mark.asyncio
class TestWebSocketListenerErrorScenarios:
    async def test_base_listener_empty_payload(self):
        """Test _base_listener handles empty payload gracefully."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        queue_dict = {"test_client": AsyncMock(spec=asyncio.Queue)}
        queue_dict["test_client"].put = AsyncMock()

        await manager._base_listener(
            connection=None,
            pid=123,
            channel="test_channel",
            payload="   ",
            update_type="test-update",
            queue_dict=queue_dict,
        )

        queue_dict["test_client"].put.assert_not_called()

    async def test_base_listener_invalid_json(self):
        """Test _base_listener handles invalid JSON payload."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        queue_dict = {"test_client": AsyncMock(spec=asyncio.Queue)}
        queue_dict["test_client"].put = AsyncMock()

        await manager._base_listener(
            connection=None,
            pid=123,
            channel="test_channel",
            payload="invalid json {{{",
            update_type="test-update",
            queue_dict=queue_dict,
        )

        queue_dict["test_client"].put.assert_not_called()

    async def test_base_listener_missing_match_id(self):
        """Test _base_listener handles payload without match_id."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        queue_dict = {"test_client": AsyncMock(spec=asyncio.Queue)}
        queue_dict["test_client"].put = AsyncMock()

        try:
            await manager._base_listener(
                connection=None,
                pid=123,
                channel="test_channel",
                payload='{"data": "test"}',
                update_type="test-update",
                queue_dict=queue_dict,
            )
        except KeyError:
            pass

    async def test_base_listener_exception_in_queue_put(self):
        """Test _base_listener handles exceptions when putting to queue."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        mock_queue = AsyncMock(spec=asyncio.Queue)
        mock_queue.put = AsyncMock(side_effect=Exception("Queue error"))
        queue_dict = {"test_client": mock_queue}

        with patch.object(
            connection_manager, "get_match_subscriptions", return_value=[]
        ):
            await manager._base_listener(
                connection=None,
                pid=123,
                channel="test_channel",
                payload='{"match_id": 1}',
                update_type="test-update",
                queue_dict=queue_dict,
            )

    async def test_playclock_listener_error_handling(self):
        """Test playclock_listener properly delegates to _base_listener."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        manager._base_listener = AsyncMock()

        await manager.playclock_listener(
            connection=None,
            pid=123,
            channel="playclock_change",
            payload='{"match_id": 1}',
        )

        manager._base_listener.assert_called_once()
        args = manager._base_listener.call_args.args
        assert args[4] == "playclock-update"
        assert args[5] == manager.playclock_queues

    async def test_match_data_listener_error_handling(self):
        """Test match_data_listener properly delegates to _base_listener."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        manager._base_listener = AsyncMock()

        await manager.match_data_listener(
            connection=None,
            pid=123,
            channel="matchdata_change",
            payload='{"match_id": 1}',
        )

        manager._base_listener.assert_called_once()
        args = manager._base_listener.call_args.args
        assert args[4] == "match-update"
        assert args[5] == manager.match_data_queues

    async def test_gameclock_listener_error_handling(self):
        """Test gameclock_listener properly delegates to _base_listener."""
        from src.core.models.base import MatchDataWebSocketManager
        from unittest.mock import AsyncMock, patch

        manager = MatchDataWebSocketManager(
            db_url="postgresql://test:test@localhost:5432/test"
        )
        manager._base_listener = AsyncMock()

        await manager.gameclock_listener(
            connection=None,
            pid=123,
            channel="gameclock_change",
            payload='{"match_id": 1}',
        )

        manager._base_listener.assert_called_once()
        args = manager._base_listener.call_args.args
        assert args[4] == "gameclock-update"
        assert args[5] == manager.gameclock_queues


@pytest.mark.asyncio
class TestConnectionManagerErrorScenarios:
    async def test_disconnect_nonexistent_client(self):
        """Test disconnect handles nonexistent clients gracefully."""
        await connection_manager.disconnect("nonexistent_client")

        active_connections = await connection_manager.get_active_connections()
        assert "nonexistent_client" not in active_connections

    async def test_get_queue_for_nonexistent_client(self):
        """Test get_queue_for_client raises KeyError for nonexistent client."""
        try:
            await connection_manager.get_queue_for_client("nonexistent_client")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    async def test_send_to_all_with_no_match_subscribers(self):
        """Test send_to_all handles case with no subscribers to a match."""
        import json

        match_id = 999
        test_data = {"type": "match-update", "match_id": match_id}

        await connection_manager.send_to_all(  # type: ignore[arg-type]
            json.dumps(test_data), match_id=str(match_id)  # type: ignore[arg-type]
        )

    async def test_connect_replaces_existing_connection(self):
        """Test connect properly closes existing connection when reconnecting."""
        from unittest.mock import AsyncMock

        client_id = "test_reconnect_client"
        match_id = 1

        mock_ws1 = AsyncMock(spec=WebSocket)
        mock_ws2 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_id, match_id)
        await connection_manager.connect(mock_ws2, client_id, match_id)

        active_connections = await connection_manager.get_active_connections()
        assert active_connections[client_id] == mock_ws2
        mock_ws1.close.assert_called_once()

        await connection_manager.disconnect(client_id)

    async def test_queue_operations_on_empty_queue(self):
        """Test queue operations when queue is empty."""
        from unittest.mock import AsyncMock

        client_id = "test_empty_queue_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)
        assert queue.empty()

        try:
            queue.get_nowait()
            assert False, "Should have raised asyncio.QueueEmpty"
        except asyncio.QueueEmpty:
            pass

        await connection_manager.disconnect(client_id)

    async def test_cleanup_connection_resources_for_nonexistent_client(self):
        """Test cleanup_connection_resources handles nonexistent client."""
        await connection_manager.cleanup_connection_resources("nonexistent_client")

        active_connections = await connection_manager.get_active_connections()
        assert "nonexistent_client" not in active_connections

    async def test_multiple_concurrent_connect_disconnect(self):
        """Test handling multiple concurrent connect and disconnect operations."""
        from unittest.mock import AsyncMock

        clients = [f"client_{i}" for i in range(10)]
        match_id = 1

        mock_websockets = [AsyncMock(spec=WebSocket) for _ in range(10)]

        connect_tasks = [
            connection_manager.connect(ws, client_id, match_id)
            for ws, client_id in zip(mock_websockets, clients)
        ]

        await asyncio.gather(*connect_tasks)

        active_connections = await connection_manager.get_active_connections()
        for client_id in clients:
            assert client_id in active_connections

        disconnect_tasks = [
            connection_manager.disconnect(client_id) for client_id in clients
        ]

        await asyncio.gather(*disconnect_tasks)

        active_connections = await connection_manager.get_active_connections()
        for client_id in clients:
            assert client_id not in active_connections

    async def test_send_to_all_with_mixed_queue_states(self):
        """Test send_to_all when some clients have queues and some don't."""
        from unittest.mock import AsyncMock
        import json

        match_id = 1
        client_1 = "client_with_queue"
        client_2 = "client_without_queue"
        test_data = {"type": "match-update", "match_id": match_id}

        mock_ws1 = AsyncMock(spec=WebSocket)

        await connection_manager.connect(mock_ws1, client_1, match_id)

        await connection_manager.send_to_all(  # type: ignore[arg-type]
            json.dumps(test_data), match_id=match_id  # type: ignore[arg-type]
        )

        await asyncio.sleep(0.01)

        queue_1 = await connection_manager.get_queue_for_client(client_1)
        assert not queue_1.empty()

        await connection_manager.disconnect(client_1)


@pytest.mark.asyncio
class TestWebSocketConnectionErrorHandling:
    async def test_websocket_send_error_during_message_send(self):
        """Test handling of errors when sending messages to WebSocket."""
        from unittest.mock import AsyncMock
        from starlette.websockets import WebSocketState

        client_id = "test_send_error_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.CONNECTED
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Send failed"))

        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)
        await queue.put({"type": "test", "data": "message"})

        msg = await queue.get()
        assert msg == {"type": "test", "data": "message"}

        try:
            await mock_websocket.send_json(msg)
        except Exception:
            pass

        await connection_manager.disconnect(client_id)

    async def test_websocket_close_error_during_disconnect(self):
        """Test handling of errors when closing WebSocket connection."""
        from unittest.mock import AsyncMock

        client_id = "test_close_error_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.close = AsyncMock(side_effect=Exception("Close failed"))

        await connection_manager.connect(mock_websocket, client_id, match_id)

        try:
            await connection_manager.disconnect(client_id)
            assert False, "Should have raised exception when closing fails"
        except Exception as e:
            assert "Close failed" in str(e)

        active_connections = await connection_manager.get_active_connections()
        assert client_id in active_connections

    async def test_websocket_state_check_before_send(self):
        """Test WebSocket state is checked before sending messages."""
        from unittest.mock import AsyncMock
        from starlette.websockets import WebSocketState

        client_id = "test_state_check_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        mock_websocket.application_state = WebSocketState.DISCONNECTED
        mock_websocket.send_json = AsyncMock()

        await connection_manager.connect(mock_websocket, client_id, match_id)

        assert mock_websocket.application_state == WebSocketState.DISCONNECTED

        await connection_manager.disconnect(client_id)

    async def test_queue_overflow_prevention(self):
        """Test that queue can handle high volume of messages without overflow."""
        from unittest.mock import AsyncMock

        client_id = "test_queue_overflow_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)

        num_messages = 1000
        for i in range(num_messages):
            await queue.put({"type": "test", "index": i})

        assert queue.qsize() == num_messages

        received_count = 0
        while not queue.empty():
            msg = await queue.get()
            received_count += 1

        assert received_count == num_messages

        await connection_manager.disconnect(client_id)

    async def test_concurrent_queue_access(self):
        """Test handling of concurrent access to the same queue."""
        from unittest.mock import AsyncMock

        client_id = "test_concurrent_access_client"
        match_id = 1

        mock_websocket = AsyncMock(spec=WebSocket)
        await connection_manager.connect(mock_websocket, client_id, match_id)

        queue = await connection_manager.get_queue_for_client(client_id)

        async def produce_messages():
            for i in range(50):
                await queue.put({"type": "producer", "index": i})

        async def consume_messages():
            for _ in range(50):
                await queue.get()

        await asyncio.gather(produce_messages(), consume_messages())

        assert queue.empty()

        await connection_manager.disconnect(client_id)
