import redis.asyncio as redis
from app.config import settings

pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True,
)

def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)