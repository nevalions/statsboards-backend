"""Token bucket rate limiter for controlling request rate."""

import asyncio
import time


class TokenBucket:
    """Token bucket rate limiter for async operations."""

    def __init__(
        self,
        rate: float,
        capacity: int | None = None,
    ) -> None:
        """
        Initialize token bucket rate limiter.

        Args:
            rate: Number of tokens per second to refill.
            capacity: Maximum number of tokens in bucket. Defaults to rate * 2.
        """
        self.rate = rate
        self.capacity = int(capacity or rate * 2)
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """
        Acquire tokens from the bucket, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire.
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.last_refill = now

            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate,
            )

            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                self.tokens = 0
                await asyncio.sleep(wait_time)
                self.last_refill = time.time()
            else:
                self.tokens -= tokens

    def _refill(self) -> None:
        """Refill tokens based on elapsed time. Must be called with lock held."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate,
        )

    def get_tokens(self) -> float:
        """
        Get current number of available tokens.

        Returns:
            Current token count.
        """
        return self.tokens
