import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.algorithms.token_bucket import is_allowed_token_bucket
from app.algorithms.sliding_window import is_allowed_sliding_window
from app.db.models import RequestLog
from app.db.postgres import AsyncSessionLocal

async def log_request(
    user_id: str | None,
    ip: str,
    endpoint: str,
    allowed: bool,
    algorithm: str,
):
    """Uses its own DB session — never shares with the request session."""
    try:
        async with AsyncSessionLocal() as session:
            log = RequestLog(
                user_id=user_id,
                ip=ip,
                endpoint=endpoint,
                allowed=allowed,
                algorithm=algorithm,
            )
            session.add(log)
            await session.commit()
    except Exception as e:
        print(f"Logging failed (non-fatal): {e}")

async def check_rate_limit(
    r: redis.Redis,
    db: AsyncSession,
    user_id: str | None,
    ip: str,
    endpoint: str,
    algorithm: str,
    limit: int,
    window_seconds: int,
) -> dict:
    results = {}

    identifiers = {"ip": ip}
    if user_id:
        identifiers["user"] = user_id

    for id_type, identifier in identifiers.items():
        key = f"ratelimit:{id_type}:{identifier}:{endpoint}"

        if algorithm == "token_bucket":
            allowed, remaining, retry_after = await is_allowed_token_bucket(
                r=r,
                key=key,
                capacity=limit,
                refill_rate=limit / window_seconds,
            )
        else:
            allowed, remaining, retry_after = await is_allowed_sliding_window(
                r=r,
                key=key,
                limit=limit,
                window_seconds=window_seconds,
            )

        results[id_type] = {
            "allowed": allowed,
            "remaining": remaining,
            "retry_after": retry_after,
        }

    final_allowed = all(v["allowed"] for v in results.values())
    min_remaining = min(v["remaining"] for v in results.values())
    max_retry = max(v["retry_after"] for v in results.values())

    # Log with its own session — no session conflict
    await log_request(
        user_id=user_id,
        ip=ip,
        endpoint=endpoint,
        allowed=final_allowed,
        algorithm=algorithm,
    )

    return {
        "allowed": final_allowed,
        "remaining": min_remaining,
        "retry_after": max_retry,
        "algorithm": algorithm,
        "checks": results,
    }