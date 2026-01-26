"""
Tests for proxy manager functionality.

Run with:
    pytest tests/test_proxy_manager.py
"""

from src.helpers.proxy_manager import ProxyHealth, ProxyInfo, ProxyManager


class TestProxyInfo:
    """Tests for ProxyInfo named tuple."""

    def test_proxy_info_with_auth(self):
        """Test ProxyInfo with authentication."""
        proxy_info = ProxyInfo(
            url="http://user:pass@host:8080",
            host="host",
            port=8080,
            username="user",
            password="pass",
        )

        assert proxy_info.url == "http://user:pass@host:8080"
        assert proxy_info.host == "host"
        assert proxy_info.port == 8080
        assert proxy_info.username == "user"
        assert proxy_info.password == "pass"

    def test_proxy_info_without_auth(self):
        """Test ProxyInfo without authentication."""
        proxy_info = ProxyInfo(
            url="http://host:8080",
            host="host",
            port=8080,
            username=None,
            password=None,
        )

        assert proxy_info.url == "http://host:8080"
        assert proxy_info.host == "host"
        assert proxy_info.port == 8080
        assert proxy_info.username is None
        assert proxy_info.password is None


class TestProxyHealth:
    """Tests for ProxyHealth named tuple."""

    def test_proxy_health_initialization(self):
        """Test ProxyHealth initializes with default values."""
        health = ProxyHealth()

        assert health.success_count == 0
        assert health.failure_count == 0
        assert health.success_rate == 1.0

    def test_proxy_health_success_rate(self):
        """Test ProxyHealth success rate calculation."""
        health = ProxyHealth(success_count=8, failure_count=2)

        assert health.success_rate == 0.8

    def test_proxy_health_success_rate_zero_total(self):
        """Test ProxyHealth success rate when total is zero."""
        health = ProxyHealth(success_count=0, failure_count=0)

        assert health.success_rate == 1.0


class TestProxyManager:
    """Tests for ProxyManager class."""

    def test_proxy_manager_empty_list(self):
        """Test ProxyManager with empty proxy list."""
        manager = ProxyManager(proxy_list="")

        assert manager.proxy_count == 0
        assert manager.is_enabled is False

    def test_proxy_manager_none_list(self):
        """Test ProxyManager with None proxy list."""
        manager = ProxyManager(proxy_list=None)

        assert manager.proxy_count == 0
        assert manager.is_enabled is False

    def test_proxy_manager_single_proxy_with_auth(self):
        """Test ProxyManager with single proxy with authentication."""
        manager = ProxyManager(proxy_list="http://user:pass@proxy.example.com:8080")

        assert manager.proxy_count == 1
        assert manager.is_enabled is True

        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.username == "user"
        assert proxy.password == "pass"

    def test_proxy_manager_single_proxy_without_auth(self):
        """Test ProxyManager with single proxy without authentication."""
        manager = ProxyManager(proxy_list="proxy.example.com:8080")

        assert manager.proxy_count == 1
        assert manager.is_enabled is True

        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.host == "proxy.example.com"
        assert proxy.port == 8080
        assert proxy.username is None
        assert proxy.password is None

    def test_proxy_manager_multiple_proxies(self):
        """Test ProxyManager with multiple proxies."""
        proxy_list = "proxy1.example.com:8080,proxy2.example.com:8081,proxy3.example.com:8082"
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 3
        assert manager.is_enabled is True

    def test_proxy_manager_mixed_formats(self):
        """Test ProxyManager with mixed proxy formats."""
        proxy_list = "http://user:pass@proxy1.com:8080,proxy2.com:8081,http://proxy3.com:8082"
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 3

    def test_proxy_manager_get_random_proxy(self):
        """Test that get_proxy returns random proxy."""
        proxy_list = "proxy1.com:8080,proxy2.com:8081,proxy3.com:8082"
        manager = ProxyManager(proxy_list=proxy_list)

        proxies = set()
        for _ in range(20):
            proxy = manager.get_proxy()
            if proxy:
                proxies.add(proxy.url)

        assert len(proxies) > 1

    def test_proxy_manager_get_proxy_with_exclude(self):
        """Test get_proxy excludes specified proxies."""
        proxy_list = "proxy1.com:8080,proxy2.com:8081,proxy3.com:8082"
        manager = ProxyManager(proxy_list=proxy_list)

        proxy = manager.get_proxy(exclude=["http://proxy1.com:8080"])
        assert proxy is not None
        assert proxy.url != "http://proxy1.com:8080"

    def test_proxy_manager_get_proxy_all_excluded(self):
        """Test get_proxy returns None when all proxies excluded."""
        proxy_list = "proxy1.com:8080,proxy2.com:8081"
        manager = ProxyManager(proxy_list=proxy_list)

        proxy = manager.get_proxy(exclude=["http://proxy1.com:8080", "http://proxy2.com:8081"])
        assert proxy is None

    def test_proxy_manager_record_success(self):
        """Test recording successful proxy request."""
        manager = ProxyManager(proxy_list="proxy.com:8080")

        proxy_url = "http://proxy.com:8080"
        manager.record_success(proxy_url)

        health = manager.get_proxy_health(proxy_url)
        assert health.success_count == 1
        assert health.failure_count == 0

    def test_proxy_manager_record_failure(self):
        """Test recording failed proxy request."""
        manager = ProxyManager(proxy_list="proxy.com:8080")

        proxy_url = "http://proxy.com:8080"
        manager.record_failure(proxy_url)

        health = manager.get_proxy_health(proxy_url)
        assert health.success_count == 0
        assert health.failure_count == 1

    def test_proxy_manager_record_multiple_events(self):
        """Test recording multiple proxy events."""
        manager = ProxyManager(proxy_list="proxy.com:8080")

        proxy_url = "http://proxy.com:8080"
        manager.record_success(proxy_url)
        manager.record_success(proxy_url)
        manager.record_failure(proxy_url)
        manager.record_success(proxy_url)

        health = manager.get_proxy_health(proxy_url)
        assert health.success_count == 3
        assert health.failure_count == 1
        assert health.success_rate == 0.75

    def test_proxy_manager_get_health_unknown_proxy(self):
        """Test getting health for unknown proxy."""
        manager = ProxyManager(proxy_list="proxy.com:8080")

        health = manager.get_proxy_health("http://unknown.com:8080")
        assert health.success_count == 0
        assert health.failure_count == 0

    def test_proxy_manager_invalid_proxy_format(self):
        """Test that invalid proxy formats are skipped."""
        proxy_list = "proxy1.com:8080,invalid-format,proxy2.com:8081"
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 2

    def test_proxy_manager_invalid_port(self):
        """Test that invalid port is handled."""
        proxy_list = "proxy1.com:invalid,proxy2.com:8080"
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 1

    def test_proxy_manager_missing_port(self):
        """Test that missing port is handled."""
        proxy_list = "proxy1.com,proxy2.com:8080"
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 1

    def test_proxy_manager_whitespace_handling(self):
        """Test that whitespace in proxy list is handled."""
        proxy_list = " proxy1.com:8080 , proxy2.com:8081 , proxy3.com:8082 "
        manager = ProxyManager(proxy_list=proxy_list)

        assert manager.proxy_count == 3

    def test_proxy_manager_https_proxy(self):
        """Test that HTTPS proxy format is supported."""
        manager = ProxyManager(proxy_list="https://proxy.com:8080")

        assert manager.proxy_count == 1

        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.url == "https://proxy.com:8080"

    def test_proxy_manager_socks5_proxy(self):
        """Test that SOCKS5 proxy format is supported."""
        manager = ProxyManager(proxy_list="socks5://proxy.com:8080")

        assert manager.proxy_count == 1

        proxy = manager.get_proxy()
        assert proxy is not None
        assert proxy.url == "socks5://proxy.com:8080"
