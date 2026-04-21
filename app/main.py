from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.postgres import engine, Base
from app.db.redis import get_redis
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Rate Limiter Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected successfully")
    except Exception as e:
        logger.warning(f"Database unavailable: {e}")

@app.get("/health")
async def health():
    redis_status = "ok"
    try:
        r = get_redis()
        await r.ping()
    except Exception as e:
        redis_status = f"error: {e}"
    return {"status": "ok", "redis": redis_status}