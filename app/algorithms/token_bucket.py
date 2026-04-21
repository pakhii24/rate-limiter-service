import time
import redis.asyncio as redis

# This Lua script runs atomically in Redis.
# Atomic means: no other command can run between our read and write.
# This is the correct way. Without this, two simultaneous requests
# could both read "1 token left", both allow, both decrement → -1 tokens.
# That's a race condition. Lua scripts in Redis are single-threaded and atomic.

TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')

local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
end

local elapsed = now - last_refill
local refill_amount = elapsed * refill_rate
tokens = math.min(capacity, tokens + refill_amount)

local allowed = 0
local remaining = math.floor(tokens)

if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, 3600)

return {allowed, remaining}
"""

async def is_allowed_token_bucket(
    r: redis.Redis,
    key: str,
    capacity: int,
    refill_rate: float,
) -> tuple[bool, int, int]:
    """
    Returns (allowed, remaining, retry_after)
    capacity     = max tokens in bucket
    refill_rate  = tokens added per second
    """
    now = time.time()

    result = await r.eval(
        TOKEN_BUCKET_SCRIPT,
        1,
        key,
        capacity,
        refill_rate,
        now,
        1,
    )

    allowed = bool(result[0])
    remaining = int(result[1])
    retry_after = 0 if allowed else int(1 / refill_rate) + 1

    return allowed, remaining, retry_after