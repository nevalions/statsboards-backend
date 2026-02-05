# Logging

- Call `setup_logging()` at module level in services and routers
- Initialize logger with short, descriptive name: `get_logger("TeamServiceDB", self)`
- Use appropriate log levels:
  - `debug`: detailed operation tracking
  - `info`: significant operations (creates, updates)
  - `warning`: expected but noteworthy situations
  - `error`: unexpected errors with exceptions

## Request ID Middleware

The application includes automatic request ID tracking via `RequestIDMiddleware` in `src/main.py`:

- Each request gets a unique ID (from `X-Request-ID` or generated UUID4)
- Available in `request.state.request_id`
- Included in response headers (`X-Request-ID`)
- Included in error responses

## Logging Middleware

Automatic request/response logging via `LoggingMiddleware` in `src/main.py`:

- Logs request start with method, path, and request_id
- Logs completion with status code, duration, and request_id
- Logs failures with error type and exception info

## Using Request IDs in Custom Code

```python
from fastapi import Request

async def my_endpoint(request: Request):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"Processing with request_id={request_id}")
```
