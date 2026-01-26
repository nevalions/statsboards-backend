"""
Tests for rate limiting functionality.

Run with:
    pytest tests/test_rate_limiter.py
"""

import asyncio
import time

import pytest

from src.helpers.rate_limiter import TokenBucket


class TestTokenBucket:
    """Tests for TokenBucket rate limiter."""

    def test_token_bucket_initialization(self):
        """Test TokenBucket initializes with correct values."""
        rate = 5.0
        capacity = 10

        bucket = TokenBucket(rate=rate, capacity=capacity)

        assert bucket.rate == rate
        assert bucket.capacity == capacity
        assert bucket.tokens == float(capacity)

    def test_token_bucket_default_capacity(self):
        """Test TokenBucket uses default capacity when not specified."""
        rate = 3.0

        bucket = TokenBucket(rate=rate)

        assert bucket.capacity == int(rate * 2)

    @pytest.mark.asyncio
    async def test_acquire_single_token(self):
        """Test acquiring a single token."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        initial_tokens = bucket.get_tokens()
        await bucket.acquire(1.0)
        remaining_tokens = bucket.get_tokens()

        assert remaining_tokens == initial_tokens - 1.0

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        initial_tokens = bucket.get_tokens()
        await bucket.acquire(3.0)
        remaining_tokens = bucket.get_tokens()

        assert remaining_tokens == initial_tokens - 3.0

    @pytest.mark.asyncio
    async def test_acquire_waits_when_empty(self):
        """Test that acquire waits when bucket is empty."""
        bucket = TokenBucket(rate=10.0, capacity=10)

        for _ in range(10):
            await bucket.acquire(1.0)

        bucket._refill()
        assert bucket.get_tokens() < 0.01

        start_time = time.time()
        await bucket.acquire(1.0)
        elapsed_time = time.time() - start_time

        assert elapsed_time >= 0.1

    @pytest.mark.asyncio
    async def test_acquire_respects_rate_limit(self):
        """Test that acquire respects the rate limit over time."""
        bucket = TokenBucket(rate=5.0, capacity=10)

        await bucket.acquire(1.0)
        await bucket.acquire(1.0)
        await bucket.acquire(1.0)
        await bucket.acquire(1.0)
        await bucket.acquire(1.0)

        assert bucket.get_tokens() <= 10

        await asyncio.sleep(1.0)

        bucket._refill()
        refilled_tokens = bucket.get_tokens()

        assert refilled_tokens >= 5.0

    @pytest.mark.asyncio
    async def test_concurrent_acquires(self):
        """Test that concurrent acquires are thread-safe."""
        bucket = TokenBucket(rate=2.0, capacity=5)

        async def acquire_tokens():
            for _ in range(5):
                await bucket.acquire(1.0)

        start_time = time.time()
        await asyncio.gather(*[acquire_tokens() for _ in range(2)])
        elapsed_time = time.time() - start_time

        assert elapsed_time >= 1.0

    @pytest.mark.asyncio
    async def test_burst_acquisition(self):
        """Test that burst acquisition works correctly."""
        bucket = TokenBucket(rate=2.0, capacity=10)

        await bucket.acquire(5.0)

        assert bucket.get_tokens() == 5.0

    @pytest.mark.asyncio
    async def test_refill_over_time(self):
        """Test that tokens refill over time."""
        bucket = TokenBucket(rate=5.0, capacity=10)

        await bucket.acquire(10.0)

        assert bucket.get_tokens() == 0

        await asyncio.sleep(1.0)

        bucket._refill()
        refilled_tokens = bucket.get_tokens()

        assert refilled_tokens >= 5.0
        assert refilled_tokens <= 10.0

    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """Test that token count never exceeds capacity."""
        bucket = TokenBucket(rate=10.0, capacity=5)

        assert bucket.get_tokens() == 5.0

        await asyncio.sleep(1.0)

        bucket._refill()
        tokens = bucket.get_tokens()

        assert tokens <= 5.0
