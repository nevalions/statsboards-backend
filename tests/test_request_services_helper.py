"""
Tests for request services helper functionality.

Run with:
    pytest tests/test_request_services_helper.py
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.helpers.request_services_helper import Response, get_url


class TestResponse:
    """Tests for Response named tuple."""

    def test_response_creation(self):
        """Test Response creation."""
        content = "test content"
        response = Response(content=content)

        assert response.content == content


class TestGetUrl:
    """Tests for get_url function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.original_rate_limiter = None
        self.original_concurrency_limiter = None
        self.original_proxy_manager = None

    def teardown(self):
        """Teardown test fixtures."""
        pass

    @pytest.mark.asyncio
    @patch("src.helpers.request_services_helper._rate_limiter")
    @patch("src.helpers.request_services_helper._concurrency_limiter")
    @patch("src.helpers.request_services_helper._proxy_manager")
    async def test_get_url_success_no_proxy(
        self, mock_proxy_manager, mock_concurrency_limiter, mock_rate_limiter
    ):
        """Test get_url succeeds without proxy."""
        mock_proxy_manager.is_enabled = False
        mock_rate_limiter.acquire = AsyncMock()
        mock_concurrency_limiter.__aenter__ = AsyncMock()
        mock_concurrency_limiter.__aexit__ = AsyncMock()

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="test content")
        mock_response.raise_for_status = MagicMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock()

        with patch("src.helpers.request_services_helper.ClientSession") as mock_session_class:
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock()

            result = await get_url("http://example.com")

            assert result is not None
            assert result.content == "test content"
            mock_rate_limiter.acquire.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.helpers.request_services_helper._rate_limiter")
    @patch("src.helpers.request_services_helper._concurrency_limiter")
    @patch("src.helpers.request_services_helper._proxy_manager")
    async def test_get_url_respects_concurrency_limit(
        self,
        mock_proxy_manager,
        mock_concurrency_limiter,
        mock_rate_limiter,
    ):
        """Test get_url can handle multiple requests with concurrency limit."""
        mock_proxy_manager.is_enabled = False
        mock_rate_limiter.acquire = AsyncMock()
        mock_concurrency_limiter.__aenter__ = AsyncMock()
        mock_concurrency_limiter.__aexit__ = AsyncMock()

        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="test content")
        mock_response.raise_for_status = MagicMock()

        mock_session = AsyncMock()
        mock_session.get = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock()

        with patch("src.helpers.request_services_helper.ClientSession") as mock_session_class:
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock()

            async def make_request():
                return await get_url("http://example.com")

            await asyncio.gather(*[make_request() for _ in range(3)])
            assert mock_rate_limiter.acquire.call_count == 3
            assert mock_concurrency_limiter.__aenter__.call_count == 3
