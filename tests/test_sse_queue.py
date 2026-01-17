from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.helpers.sse_queue import MatchEventQueue


class TestMatchEventQueue:
    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    @pytest.fixture
    def mock_model(self):
        class MockModel:
            def __init__(self):
                self.id = 1
                self.name = "Test"

        return MockModel()

    @pytest.fixture
    def queue(self, mock_redis, mock_model):
        return MatchEventQueue(mock_model, mock_redis, match_data_id=123)

    def test_init(self, queue, mock_redis, mock_model):
        assert queue.redis is mock_redis
        assert queue.model is mock_model
        assert queue.match_data_id == 123
        assert queue.pubsub_gameclock_channel == "match_event_queue_channel:123"
        assert queue.pubsub_gameclock is None

    @pytest.mark.asyncio
    async def test_put_redis(self, queue, mock_redis):
        data = {"key": "value"}

        await queue.put_redis(data)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "match_event_queue:123"

    @pytest.mark.asyncio
    async def test_put_redis_with_datetime(self, queue, mock_redis):
        data = {"timestamp": datetime(2023, 1, 1, 12, 0, 0)}

        await queue.put_redis(data)

        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_put_redis_non_serializable_raises(self, queue, mock_redis):
        class NonSerializable:
            pass

        with pytest.raises(TypeError):
            await queue.put_redis({"obj": NonSerializable()})

    @pytest.mark.asyncio
    async def test_get_redis_exists(self, queue, mock_redis):
        mock_redis.exists.return_value = 1
        mock_redis.get.return_value = '{"key": "value"}'

        result = await queue.get_redis()

        assert result == {"key": "value"}
        mock_redis.exists.assert_called_once_with("match_event_queue:123")
        mock_redis.get.assert_called_once_with("match_event_queue:123")

    @pytest.mark.asyncio
    async def test_get_redis_not_exists(self, queue, mock_redis):
        mock_redis.exists.return_value = 0

        result = await queue.get_redis()

        assert result is None
        mock_redis.exists.assert_called_once_with("match_event_queue:123")
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_redis_exists_but_no_data(self, queue, mock_redis):
        mock_redis.exists.return_value = 1
        mock_redis.get.return_value = None

        result = await queue.get_redis()

        assert result is None
        mock_redis.exists.assert_called_once()
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_setup_pubsub_gameclock(self, queue, mock_redis):
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

        await queue.redis_setup_pubsub_gameclock()

        mock_redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once_with("match_event_queue_channel:123")
        assert queue.pubsub_gameclock is mock_pubsub

    @pytest.mark.asyncio
    async def test_redis_publish_event(self, queue, mock_redis):
        data = {"event": "test"}

        await queue.redis_publish_event(data)

        mock_redis.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_publish_event_with_datetime(self, queue, mock_redis):
        data = {"time": datetime(2023, 1, 1, 12, 0, 0)}

        await queue.redis_publish_event(data)

        mock_redis.publish.assert_called_once()

    def test_default_serializer_datetime(self):
        result = MatchEventQueue.default_serializer(datetime(2023, 1, 1, 12, 0, 0))
        assert result == "2023-01-01T12:00:00"

    def test_default_serializer_unsupported_type(self):
        with pytest.raises(TypeError):
            MatchEventQueue.default_serializer(object())
