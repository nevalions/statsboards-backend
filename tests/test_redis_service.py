from unittest.mock import AsyncMock, patch

import pytest

from src.core.redis import RedisService
from src.helpers.sse_queue import MatchEventQueue


class TestRedisService:
    @pytest.fixture
    def redis_service(self):
        return RedisService(redis_url="redis://localhost:6379")

    def test_init(self, redis_service):
        assert redis_service.redis_url == "redis://localhost:6379"

    def test_init_default_url(self):
        service = RedisService()
        assert service.redis_url == "redis://localhost:6379"

    @pytest.mark.asyncio
    async def test_create_match_event_queue(self, redis_service):
        with patch.object(redis_service, "create_redis_connection") as mock_create_conn:
            mock_redis = AsyncMock()
            mock_create_conn.return_value = mock_redis

            result = await redis_service.create_match_event_queue(123)

            assert isinstance(result, MatchEventQueue)
            mock_create_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_match_event_queue_exists(self, redis_service):
        with patch.object(redis_service, "create_match_event_queue") as mock_create:
            mock_queue = AsyncMock()
            mock_create.return_value = mock_queue
            mock_queue.get_redis.return_value = {"data": "exists"}

            match_data = {"game_status": "in-progress"}
            result = await redis_service.get_match_event_queue(123, match_data)

            assert result is mock_queue
            mock_queue.get_redis.assert_called_once()
            mock_queue.put_redis.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_match_event_queue_not_exists(self, redis_service):
        with patch.object(redis_service, "create_match_event_queue") as mock_create:
            mock_queue = AsyncMock()
            mock_create.return_value = mock_queue
            mock_queue.get_redis.return_value = None

            match_data = {"game_status": "in-progress"}
            result = await redis_service.get_match_event_queue(123, match_data)

            assert result is mock_queue
            mock_queue.get_redis.assert_called_once()
            mock_queue.put_redis.assert_called_once_with(match_data)

    @pytest.mark.asyncio
    async def test_get_match_event_queue_no_match_data(self, redis_service):
        with patch.object(redis_service, "create_match_event_queue") as mock_create:
            mock_queue = AsyncMock()
            mock_create.return_value = mock_queue
            mock_queue.get_redis.return_value = None

            result = await redis_service.get_match_event_queue(123, None)

            assert result is mock_queue
            mock_queue.get_redis.assert_called_once()
            mock_queue.put_redis.assert_called_once_with(None)
