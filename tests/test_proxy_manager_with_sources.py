"""
Tests for proxy manager with URL fetching.

Run with:
    pytest tests/test_proxy_manager_with_sources.py
"""

from src.helpers.proxy_manager import ProxyHealth, ProxyManager


class TestProxyManagerUrlFetching:
    """Tests for ProxyManager with URL fetching."""

    def test_parse_simple_ip_port_format(self):
        """Test parsing simple IP:PORT format."""
        manager = ProxyManager()

        proxy_info = manager._parse_proxy_string("185.193.29.223:80")

        assert proxy_info.url == "http://185.193.29.223:80"
        assert proxy_info.host == "185.193.29.223"
        assert proxy_info.port == 80
        assert proxy_info.username is None
        assert proxy_info.password is None

    def test_parse_multiple_simple_formats(self):
        """Test parsing multiple simple IP:PORT proxies."""
        manager = ProxyManager()

        proxy_info1 = manager._parse_proxy_string("104.24.76.27:80")
        proxy_info2 = manager._parse_proxy_string("172.67.70.251:8080")

        assert proxy_info1.host == "104.24.76.27"
        assert proxy_info1.port == 80
        assert proxy_info2.host == "172.67.70.251"
        assert proxy_info2.port == 8080

    def test_parse_mixed_static_and_fetched_proxies(self):
        """Test combining static and fetched proxies."""
        manager = ProxyManager(
            proxy_list="http://static1.com:8080,http://static2.com:8081",
        )

        proxy_info3 = manager._parse_proxy_string("185.193.29.223:80")
        proxy_info4 = manager._parse_proxy_string("104.24.76.27:80")

        manager.proxies.extend([proxy_info3, proxy_info4])
        manager.health["http://185.193.29.223:80"] = ProxyHealth()
        manager.health["http://104.24.76.27:80"] = ProxyHealth()

        assert manager.proxy_count == 4

    def test_proxy_manager_no_sources(self):
        """Test ProxyManager with no sources."""
        manager = ProxyManager()

        assert manager.proxy_count == 0
        assert manager.is_enabled is False

    def test_proxy_manager_initializes_source_urls(self):
        """Test that proxy source URLs are properly initialized."""
        source_urls = "http://example.com/proxies.txt,http://example2.com/proxies.txt"
        manager = ProxyManager(proxy_source_urls=source_urls)

        assert manager._source_urls == [
            "http://example.com/proxies.txt",
            "http://example2.com/proxies.txt",
        ]

    def test_proxy_manager_initializes_without_sources(self):
        """Test ProxyManager initializes without sources."""
        manager = ProxyManager(proxy_source_urls=None)

        assert manager._source_urls == []
        assert not manager._source_urls
