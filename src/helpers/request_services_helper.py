from random import uniform
from typing import NamedTuple

from aiohttp import ClientConnectorError, ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from ..logging_config import get_logger

logger = get_logger("backend_logger_request_services")


class Response(NamedTuple):
    content: str


async def get_url(url: str):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "3600",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) "
        "Gecko/20100101 Firefox/52.0",
    }
    timeout_val = uniform(0.5, 0.9)

    try:
        async with ClientSession() as session:
            async with session.get(
                url=url,
                headers=headers,
                timeout=ClientTimeout(total=timeout_val),
                ssl=False,
            ) as response:
                response.raise_for_status()
                text_content = await response.text()
                return Response(content=text_content)
    except ClientConnectorError as e:
        logger.warning(f"Cannot connect to host {url}. Connection failed: {e}")
        return None
    except ClientError as e:
        logger.warning(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error fetching URL {url}: {e}", exc_info=True)
        return None
