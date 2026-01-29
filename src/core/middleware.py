import uuid
from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.logging_config import get_logger

logger = get_logger("fastapi")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate unique request IDs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request/response information with timing and request IDs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = perf_counter()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration_ms = (perf_counter() - start_time) * 1000

            if response.status_code >= 400:
                logger.warning(
                    f"Request completed: {method} {path} - "
                    f"status={response.status_code} "
                    f"duration={duration_ms:.2f}ms "
                    f"request_id={request_id}"
                )
            else:
                logger.debug(
                    f"Request completed: {method} {path} - "
                    f"status={response.status_code} "
                    f"duration={duration_ms:.2f}ms "
                    f"request_id={request_id}"
                )

            return response
        except Exception as e:
            duration_ms = (perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed: {method} {path} - "
                f"error={type(e).__name__} "
                f"duration={duration_ms:.2f}ms "
                f"request_id={request_id}",
                exc_info=True,
            )
            raise
