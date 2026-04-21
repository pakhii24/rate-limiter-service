from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.schemas import CheckRequest, CheckResponse
from app.db.redis import get_redis
from app.db.postgres import get_db
from app.services.rate_limiter import check_rate_limit
from app.services.rule_engine import get_rule
from app.db.models import Rule
import redis.asyncio as redis

router = APIRouter()

@router.post("/check", response_model=CheckResponse)
async def check(
    request: CheckRequest,
    r: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    rule = await get_rule(request.endpoint, db, r)

    result = await check_rate_limit(
        r=r,
        db=db,
        user_id=request.user_id,
        ip=request.ip,
        endpoint=request.endpoint,
        algorithm=rule["algorithm"],
        limit=rule["limit"],
        window_seconds=rule["window_seconds"],
    )
    return CheckResponse(
        allowed=result["allowed"],
        remaining=result["remaining"],
        retry_after=result["retry_after"],
        algorithm=result["algorithm"],
    )

@router.get("/rules")
async def get_rules(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Rule))
    rules = result.scalars().all()
    return {"rules": [
        {
            "id": r.id,
            "endpoint": r.endpoint,
            "algorithm": r.algorithm,
            "limit": r.limit,
            "window_seconds": r.window_seconds,
        } for r in rules
    ]}

@router.post("/rules")
async def create_rule(
    endpoint: str,
    algorithm: str,
    limit: int,
    window_seconds: int,
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    rule = Rule(
        endpoint=endpoint,
        algorithm=algorithm,
        limit=limit,
        window_seconds=window_seconds,
    )
    db.add(rule)
    await db.commit()
    await r.delete(f"rule:{endpoint}")
    return {"message": "Rule created", "endpoint": endpoint}

@router.get("/logs")
async def get_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
):
    from sqlalchemy import desc
    from app.db.models import RequestLog
    result = await db.execute(
        select(RequestLog).order_by(desc(RequestLog.timestamp)).limit(limit)
    )
    logs = result.scalars().all()
    return {"logs": [
        {
            "id": l.id,
            "user_id": l.user_id,
            "ip": l.ip,
            "endpoint": l.endpoint,
            "allowed": l.allowed,
            "algorithm": l.algorithm,
            "timestamp": l.timestamp,
        } for l in logs
    ]}