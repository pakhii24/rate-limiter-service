import pytest
import pytest_asyncio
import redis.asyncio as redis
from app.algorithms.token_bucket import is_allowed_token_bucket

@pytest_asyncio.fixture
async def r():
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    yield client
    await client.aclose()

@pytest.mark.asyncio
async def test_allows_within_limit(r):
    key = "test:tb:within_limit"
    await r.delete(key)
    allowed, remaining, _ = await is_allowed_token_bucket(r, key, capacity=5, refill_rate=1.0)
    assert allowed is True
    assert remaining == 5

@pytest.mark.asyncio
async def test_blocks_when_empty(r):
    key = "test:tb:blocks"
    await r.delete(key)
    for _ in range(5):
        await is_allowed_token_bucket(r, key, capacity=5, refill_rate=1.0)
    allowed, remaining, retry_after = await is_allowed_token_bucket(r, key, capacity=5, refill_rate=1.0)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0

@pytest.mark.asyncio
async def test_remaining_decrements(r):
    key = "test:tb:decrement"
    await r.delete(key)
    _, r1, _ = await is_allowed_token_bucket(r, key, capacity=10, refill_rate=1.0)
    _, r2, _ = await is_allowed_token_bucket(r, key, capacity=10, refill_rate=1.0)
    assert r2 < r1