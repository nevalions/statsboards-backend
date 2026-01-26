"""HTTP client services for making external requests."""

import asyncio
from random import uniform
from typing import NamedTuple

from aiohttp import ClientConnectorError, ClientProxyConnectionError, ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from ..core.config import settings
from ..logging_config import get_logger
from .proxy_manager import ProxyManager
from .rate_limiter import TokenBucket

logger = get_logger("backend_logger_request_services")

_rate_limiter = TokenBucket(rate=settings.rate_limit_requests_per_second)
_concurrency_limiter = asyncio.Semaphore(settings.rate_limit_max_concurrent)
_proxy_manager = ProxyManager(
    proxy_list=settings.proxy_list,
    proxy_source_urls=settings.proxy_source_urls,
)


async def initialize_proxy_manager() -> None:
    """
    Initialize proxy manager by fetching proxies from sources if configured.

    Should be called during application startup.
    """
    await _proxy_manager.fetch_proxies_from_sources()
    logger.info(f"Proxy manager initialized with {_proxy_manager.proxy_count} proxies")


class Response(NamedTuple):
    content: str


async def get_url(
    url: str,
    use_proxy: bool = True,
    timeout: float | None = None,
) -> Response | None:
    """
    Fetch URL content with rate limiting and optional proxy support.

    Args:
        url: URL to fetch.
        use_proxy: Whether to use proxy if configured.
        timeout: Optional timeout in seconds. Defaults to random 0.5-0.9s.

    Returns:
        Response with content, or None on failure.
    """
    timeout_val = timeout if timeout is not None else uniform(0.5, 0.9)

    async with _concurrency_limiter:
        await _rate_limiter.acquire()

        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) "
            "Gecko/20100101 Firefox/52.0",
        }

        proxy_url: str | None = None
        excluded_proxies: list[str] = []

        if use_proxy and _proxy_manager.is_enabled:
            proxy_info = _proxy_manager.get_proxy(exclude=excluded_proxies)
            if proxy_info:
                proxy_url = proxy_info.url

        max_retries = settings.proxy_max_retries if use_proxy and _proxy_manager.is_enabled else 1

        for attempt in range(max_retries):
            try:
                async with ClientSession() as session:
                    async with session.get(
                        url=url,
                        headers=headers,
                        timeout=ClientTimeout(total=timeout_val),
                        ssl=False,
                        proxy=proxy_url,
                    ) as response:
                        response.raise_for_status()
                        text_content = await response.text()

                        if proxy_url:
                            _proxy_manager.record_success(proxy_url)

                        return Response(content=text_content)

            except ClientProxyConnectionError as e:
                if proxy_url:
                    logger.warning(
                        f"Proxy connection failed (attempt {attempt + 1}/{max_retries}): {proxy_url} - {e}"
                    )
                    _proxy_manager.record_failure(proxy_url)
                    excluded_proxies.append(proxy_url)

                    if attempt < max_retries - 1:
                        proxy_info = _proxy_manager.get_proxy(exclude=excluded_proxies)
                        proxy_url = proxy_info.url if proxy_info else None
                        if not proxy_url:
                            logger.warning("No more proxies available, continuing without proxy")
                            proxy_url = None
                        continue
                else:
                    logger.warning(f"Proxy connection error: {e}")
                    return None

            except ClientConnectorError as e:
                logger.warning(f"Cannot connect to host {url}. Connection failed: {e}")
                return None

            except ClientError as e:
                logger.warning(f"Error fetching URL {url}: {e}")
                return None

            except Exception as e:
                logger.warning(f"Unexpected error fetching URL {url}: {e}", exc_info=True)
                return None

        return None
