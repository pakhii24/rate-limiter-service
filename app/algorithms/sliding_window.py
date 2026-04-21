import time
import uuid
import redis.asyncio as redis

async def is_allowed_sliding_window(
    r: redis.Redis,
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int, int]:
    now = time.time()
    window_start = now - window_seconds

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.expire(key, window_seconds * 2)
    results = await pipe.execute()

    request_count = results[1]

    if request_count < limit:
        # Use unique member key — fixes collision when two requests
        # arrive at the exact same millisecond
        member = f"{now}:{uuid.uuid4()}"
        await r.zadd(key, {member: now})
        allowed = True
        remaining = limit - request_count - 1
        retry_after = 0
    else:
        allowed = False
        remaining = 0
        retry_after = window_seconds

    return allowed, remaining, retry_after