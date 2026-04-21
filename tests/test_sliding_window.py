import pytest
import pytest_asyncio
import redis.asyncio as redis
from app.algorithms.sliding_window import is_allowed_sliding_window

@pytest_asyncio.fixture
async def r():
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    yield client
    await client.aclose()

@pytest.mark.asyncio
async def test_allows_within_limit(r):
    key = "test:sw:within_limit"
    await r.delete(key)
    allowed, remaining, _ = await is_allowed_sliding_window(r, key, limit=5, window_seconds=60)
    assert allowed is True
    assert remaining == 4

@pytest.mark.asyncio
async def test_blocks_over_limit(r):
    key = "test:sw:blocks"
    await r.delete(key)
    for _ in range(5):
        await is_allowed_sliding_window(r, key, limit=5, window_seconds=60)
    allowed, remaining, retry_after = await is_allowed_sliding_window(r, key, limit=5, window_seconds=60)
    assert allowed is False
    assert remaining == 0
    assert retry_after == 60

@pytest.mark.asyncio
async def test_no_burst_allowance(r):
    """Sliding window is strict — no burst. Unlike token bucket."""
    key = "test:sw:no_burst"
    await r.delete(key)
    results = []
    for _ in range(7):
        allowed, _, _ = await is_allowed_sliding_window(r, key, limit=5, window_seconds=60)
        results.append(allowed)
    assert results[:5] == [True, True, True, True, True]
    assert results[5:] == [False, False]