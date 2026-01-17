from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.matches.websocket_stats_router import MatchStatsWebSocketRouter


class TestMatchStatsWebSocketRouter:
    @pytest.fixture
    def mock_service(self):
        return MagicMock()

    @pytest.fixture
    def mock_stats_service(self):
        return MagicMock()

    @pytest.fixture
    def router(self, mock_service, mock_stats_service):
        with patch("src.matches.websocket_stats_router.MatchStatsWebSocketHandler"):
            return MatchStatsWebSocketRouter(service=mock_service, stats_service=mock_stats_service)

    def test_init(self, router, mock_service, mock_stats_service):
        assert router.service is mock_service
        assert router.stats_service is mock_stats_service
        assert router.prefix == "/api/matches"
        assert router.tags == ["matches-stats-websocket"]
        assert router.logger is not None
        assert router.stats_handler is not None

    def test_route_returns_router(self, router):
        with patch.object(router.stats_handler, "handle_websocket_connection") as mock_handle:
            mock_handle.return_value = AsyncMock()

            result = router.route()

            assert result is not None
            assert hasattr(result, "routes")

    def test_route_websocket_endpoint(self, router):
        with patch.object(router.stats_handler, "handle_websocket_connection") as mock_handle:
            mock_handle.return_value = AsyncMock()

            api_router = router.route()
            routes = list(api_router.routes)

            assert len(routes) > 0

    @pytest.mark.asyncio
    async def test_websocket_endpoint_calls_handler(self, router):
        mock_websocket = AsyncMock()
        mock_websocket.__id__ = 12345

        with patch.object(router.stats_handler, "handle_websocket_connection") as mock_handle:
            mock_handle.return_value = AsyncMock()

            api_router = router.route()

            for route in api_router.routes:
                if hasattr(route, "websocket"):
                    websocket_func = route.endpoint
                    await websocket_func(mock_websocket, 999)

                    mock_handle.assert_called_once_with(
                        mock_websocket, f"{mock_websocket.__id__}", 999
                    )
                    break
