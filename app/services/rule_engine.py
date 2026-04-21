from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Rule
import redis.asyncio as redis
import json

DEFAULT_RULES = {
    "default": {
        "algorithm": "sliding_window",
        "limit": 60,
        "window_seconds": 60,
    }
}

async def get_rule(
    endpoint: str,
    db: AsyncSession,
    r: redis.Redis,
) -> dict:
    """
    Lookup order:
    1. Redis cache (fast, <1ms)
    2. Postgres (slower, but only on cache miss)
    3. Default fallback
    """
    cache_key = f"rule:{endpoint}"

    # 1. Check Redis cache first
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. Check Postgres
    try:
        result = await db.execute(
            select(Rule).where(Rule.endpoint == endpoint)
        )
        rule = result.scalar_one_or_none()

        if rule:
            rule_dict = {
                "algorithm": rule.algorithm,
                "limit": rule.limit,
                "window_seconds": rule.window_seconds,
            }
            # Cache it in Redis for 5 minutes
            await r.setex(cache_key, 300, json.dumps(rule_dict))
            return rule_dict
    except Exception:
        pass

    # 3. Return default
    return DEFAULT_RULES["default"]