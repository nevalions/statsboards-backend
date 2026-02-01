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

    @pytest.mark.asyncio
    @patch("src.helpers.request_services_helper._rate_limiter")
    @patch("src.helpers.request_services_helper._concurrency_limiter")
    @patch("src.helpers.request_services_helper._proxy_manager")
    @patch("src.helpers.request_services_helper.get_random_user_agent")
    async def test_headers_include_user_agent_and_referer(
        self,
        mock_get_random_user_agent,
        mock_proxy_manager,
        mock_concurrency_limiter,
        mock_rate_limiter,
    ):
        """Test get_url sets proper headers including User-Agent and Referer."""
        mock_proxy_manager.is_enabled = False
        mock_rate_limiter.acquire = AsyncMock()
        mock_concurrency_limiter.__aenter__ = AsyncMock()
        mock_concurrency_limiter.__aexit__ = AsyncMock()

        test_url = "https://fafr.su/tournament/28"
        mock_get_random_user_agent.return_value = "Mozilla/5.0 (Test Browser)"

        captured_headers = {}

        def capture_headers(url, headers, **kwargs):
            captured_headers.update(headers)
            mock_response = AsyncMock()
            mock_response.text = AsyncMock(return_value="test content")
            mock_response.raise_for_status = MagicMock()
            return MagicMock(
                __aenter__=AsyncMock(return_value=mock_response), __aexit__=AsyncMock()
            )

        mock_session = AsyncMock()
        mock_session.get = MagicMock(side_effect=capture_headers)

        with patch("src.helpers.request_services_helper.ClientSession") as mock_session_class:
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock()

            result = await get_url(test_url)

            assert result is not None
            assert "User-Agent" in captured_headers
            assert captured_headers["User-Agent"] == "Mozilla/5.0 (Test Browser)"
            assert "Referer" in captured_headers
            assert captured_headers["Referer"] == "https://fafr.su"
            assert "Accept" in captured_headers
            assert "Accept-Language" in captured_headers
            assert "Accept-Encoding" in captured_headers
            assert "DNT" in captured_headers
            assert "Sec-Fetch-Site" in captured_headers
            assert captured_headers["Sec-Fetch-Site"] == "same-origin"

    @pytest.mark.asyncio
    @patch("src.helpers.request_services_helper._rate_limiter")
    @patch("src.helpers.request_services_helper._concurrency_limiter")
    @patch("src.helpers.request_services_helper._proxy_manager")
    async def test_rate_limiting_uses_correct_rate(
        self,
        mock_proxy_manager,
        mock_concurrency_limiter,
        mock_rate_limiter,
    ):
        """Test rate limiter uses the configured rate."""
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
            mock_rate_limiter.acquire.assert_called_once()
