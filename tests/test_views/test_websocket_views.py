import asyncio
import pytest
from starlette.websockets import WebSocket

from src.core.models.base import connection_manager
from src.logging_config import setup_logging

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

        await connection_manager.send_to_all(json.dumps(test_data), match_id=match_id)

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
        await connection_manager.send_to_all(json.dumps(test_data), match_id=match_1)

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
