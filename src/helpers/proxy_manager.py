"""Proxy manager for handling proxy rotation, health tracking, and URL fetching."""

import asyncio
import random
import time
from typing import NamedTuple

import aiohttp
from aiohttp import ClientTimeout

from ..core.config import settings
from ..logging_config import get_logger

logger = get_logger("backend_logger_proxy_manager")


class ProxyInfo(NamedTuple):
    """Information about a proxy."""

    url: str
    host: str
    port: int
    username: str | None = None
    password: str | None = None


class ProxyHealth(NamedTuple):
    """Health statistics for a proxy."""

    success_count: int = 0
    failure_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total


class ProxyManager:
    """Manages proxy selection, health tracking, and URL fetching."""

    def __init__(
        self,
        proxy_list: str | None = None,
        proxy_source_urls: str | None = None,
    ) -> None:
        """
        Initialize proxy manager.

        Args:
            proxy_list: Comma-separated list of proxy URLs.
            proxy_source_urls: Comma-separated list of URLs to fetch proxies from.
        """
        self.proxies: list[ProxyInfo] = []
        self.health: dict[str, ProxyHealth] = {}
        self.cache_expiry: float = 0
        self._parse_proxy_list(proxy_list or "")

        if proxy_source_urls:
            self._source_urls = [url.strip() for url in proxy_source_urls.split(",")]
        else:
            self._source_urls = []

    def _parse_proxy_list(self, proxy_list: str) -> None:
        """
        Parse and validate proxy list.

        Supports formats:
        - http://user:pass@host:port
        - http://host:port
        - host:port
        - IP:PORT (simple format, e.g., 185.193.29.223:80)

        Args:
            proxy_list: Comma-separated list of proxy URLs.
        """
        for proxy_str in proxy_list.split(","):
            proxy_str = proxy_str.strip()
            if not proxy_str:
                continue

            try:
                proxy_info = self._parse_proxy_string(proxy_str)
                self.proxies.append(proxy_info)
                self.health[proxy_info.url] = ProxyHealth()
                logger.info(f"Added proxy: {proxy_info.host}:{proxy_info.port}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid proxy format '{proxy_str}': {e}")

        logger.info(f"Proxy manager initialized with {len(self.proxies)} proxies")

    def _parse_proxy_string(self, proxy_str: str) -> ProxyInfo:
        """
        Parse a single proxy string into ProxyInfo.

        Args:
            proxy_str: Proxy URL string.

        Returns:
            ProxyInfo object.

        Raises:
            ValueError: If proxy format is invalid.
        """
        normalized = proxy_str

        if not normalized.startswith(("http://", "https://", "socks://", "socks5://")):
            if "@" in normalized:
                normalized = f"http://{normalized}"
            else:
                normalized = f"http://{normalized}"

        if normalized.startswith("http://"):
            rest = normalized[7:]
        elif normalized.startswith("https://"):
            rest = normalized[8:]
        elif normalized.startswith("socks://"):
            rest = normalized[7:]
        elif normalized.startswith("socks5://"):
            rest = normalized[8:]
        else:
            raise ValueError(f"Unsupported proxy scheme in '{proxy_str}'")

        username: str | None = None
        password: str | None = None

        if "@" in rest:
            auth_part, host_port = rest.split("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                raise ValueError(f"Invalid auth format in '{proxy_str}'")
        else:
            host_port = rest

        if ":" not in host_port:
            raise ValueError(f"Missing port in '{proxy_str}'")

        host, port_str = host_port.split(":", 1)

        try:
            port = int(port_str)
            if not 1 <= port <= 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            raise ValueError(f"Invalid port '{port_str}'") from e

        return ProxyInfo(
            url=normalized,
            host=host,
            port=port,
            username=username,
            password=password,
        )

    async def fetch_proxies_from_sources(self) -> None:
        """
        Fetch proxies from configured source URLs.

        Fetches are cached based on TTL to avoid repeated fetches.
        """
        if not self._source_urls:
            return

        current_time = time.time()
        if current_time < self.cache_expiry:
            logger.info("Using cached proxy list")
            return

        logger.info(f"Fetching proxies from {len(self._source_urls)} sources")

        all_proxies: set[str] = set()

        async with aiohttp.ClientSession(
            timeout=ClientTimeout(total=settings.proxy_source_fetch_timeout)
        ) as session:
            tasks = [self._fetch_from_url(url, session) for url in self._source_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for url, result in zip(self._source_urls, results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch from {url}: {result}")
                elif isinstance(result, list):
                    is_socks5_source = "socks5" in url.lower()

                    for proxy_str in result:
                        proxy_str = proxy_str.strip()
                        if not proxy_str:
                            continue

                        try:
                            if is_socks5_source and not proxy_str.startswith(
                                ("socks://", "socks5://", "http://", "https://")
                            ):
                                proxy_str = f"socks5://{proxy_str}"

                            proxy_info = self._parse_proxy_string(proxy_str)
                            if proxy_info.url not in all_proxies:
                                all_proxies.add(proxy_info.url)
                                logger.info(f"Fetched proxy: {proxy_info.host}:{proxy_info.port}")
                        except Exception as e:
                            logger.warning(f"Invalid proxy format from {url}: '{proxy_str}': {e}")

        self._add_fetched_proxies(list(all_proxies))
        self.cache_expiry = current_time + settings.proxy_source_cache_ttl
        logger.info(f"Proxy cache expires at {self.cache_expiry}")

    async def _fetch_from_url(self, url: str, session: aiohttp.ClientSession) -> list[str] | None:
        """
        Fetch proxy list from a URL.

        Args:
            url: URL to fetch proxies from.
            session: aiohttp ClientSession.

        Returns:
            List of proxy strings, or None on failure.
        """
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch from {url}: HTTP {response.status}")
                    return None

                text_content = await response.text()
                proxies = [line.strip() for line in text_content.split("\n") if line.strip()]

                logger.info(f"Fetched {len(proxies)} proxies from {url}")
                return proxies
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
            raise

    def _add_fetched_proxies(self, proxy_urls: list[str]) -> None:
        """
        Add fetched proxies to the proxy list.

        Args:
            proxy_urls: List of proxy URLs to add.
        """
        max_proxies = settings.proxy_source_max_proxies

        random.shuffle(proxy_urls)
        proxy_urls = proxy_urls[:max_proxies]

        for proxy_url in proxy_urls:
            if proxy_url in self.health:
                continue

            try:
                proxy_info = self._parse_proxy_string(proxy_url)
                self.proxies.append(proxy_info)
                self.health[proxy_info.url] = ProxyHealth()
                logger.info(f"Added fetched proxy: {proxy_info.host}:{proxy_info.port}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid fetched proxy format '{proxy_url}': {e}")

        logger.info(f"Total proxies after fetch: {len(self.proxies)}")

    async def refresh_proxies_if_needed(self) -> None:
        """
        Refresh proxy list if cache has expired.
        """
        if self._source_urls:
            await self.fetch_proxies_from_sources()

    def get_proxy(self, exclude: list[str] | None = None) -> ProxyInfo | None:
        """
        Get a random proxy, excluding specified ones.

        Args:
            exclude: List of proxy URLs to exclude.

        Returns:
            ProxyInfo or None if no proxies available.
        """
        exclude = exclude or []

        available = [p for p in self.proxies if p.url not in exclude]

        if not available:
            return None

        return random.choice(available)

    def record_success(self, proxy_url: str) -> None:
        """
        Record a successful request through a proxy.

        Args:
            proxy_url: URL of the proxy.
        """
        if proxy_url not in self.health:
            return

        current = self.health[proxy_url]
        self.health[proxy_url] = ProxyHealth(
            success_count=current.success_count + 1,
            failure_count=current.failure_count,
        )

    def record_failure(self, proxy_url: str) -> None:
        """
        Record a failed request through a proxy.

        Args:
            proxy_url: URL of the proxy.
        """
        if proxy_url not in self.health:
            return

        current = self.health[proxy_url]
        self.health[proxy_url] = ProxyHealth(
            success_count=current.success_count,
            failure_count=current.failure_count + 1,
        )

    def get_proxy_health(self, proxy_url: str) -> ProxyHealth:
        """
        Get health statistics for a proxy.

        Args:
            proxy_url: URL of the proxy.

        Returns:
            ProxyHealth object.
        """
        return self.health.get(proxy_url, ProxyHealth())

    @property
    def proxy_count(self) -> int:
        """Get number of configured proxies."""
        return len(self.proxies)

    @property
    def is_enabled(self) -> bool:
        """Check if proxy support is enabled."""
        return len(self.proxies) > 0
