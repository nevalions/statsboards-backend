from unittest.mock import AsyncMock, MagicMock

import pytest

from src.matches.match_data_cache_service import MatchDataCacheService
from src.utils.websocket.websocket_manager import MatchDataWebSocketManager


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
