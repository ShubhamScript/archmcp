"""Tests for sliding window rate limiter and middleware."""

from archmcp.auth.rate_limiter import InMemoryRateLimiter


def test_in_memory_rate_limiter_burst_and_exhaustion():
    limiter = InMemoryRateLimiter(limit=3, window_seconds=2)
    limiter.reset()

    client_id = "test-token-123"

    # Request 1: allowed
    allowed, remaining, reset = limiter.is_allowed(client_id)
    assert allowed is True
    assert remaining == 2

    # Request 2: allowed
    allowed, remaining, reset = limiter.is_allowed(client_id)
    assert allowed is True
    assert remaining == 1

    # Request 3: allowed (last of window)
    allowed, remaining, reset = limiter.is_allowed(client_id)
    assert allowed is True
    assert remaining == 0

    # Request 4: rejected (exhausted limit)
    allowed, remaining, reset = limiter.is_allowed(client_id)
    assert allowed is False
    assert remaining == 0
    assert reset > 0


def test_in_memory_rate_limiter_client_isolation():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=2)
    limiter.reset()

    # Exhaust Client A
    limiter.is_allowed("client-a")
    limiter.is_allowed("client-a")
    assert limiter.is_allowed("client-a")[0] is False

    # Client B should still be allowed
    assert limiter.is_allowed("client-b")[0] is True
