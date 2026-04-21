# Rate Limiter as a Service

A distributed rate limiting service implementing Token Bucket and Sliding Window algorithms, deployed on AWS EC2.

## Architecture
Client → FastAPI Service → Redis (allow/block decision, <1ms)
→ PostgreSQL (async request logging)
→ React Dashboard (real-time metrics)
## Algorithms

### Token Bucket
- Allows short bursts
- Atomic Lua script in Redis prevents race conditions
- Key insight: without Lua, two concurrent requests could both read "1 token left" and both pass — a classic TOCTOU race condition

### Sliding Window
- Strict fairness, no burst allowance
- Redis sorted sets (ZADD/ZREMRANGEBYSCORE/ZCARD)
- Higher memory cost than fixed window but more accurate

## Features
- Per-user AND per-IP throttling simultaneously
- Admin-configurable rules per endpoint (stored in Postgres, cached in Redis)
- Real-time React dashboard with live metrics
- Async request logging (never blocks the allow/block path)
- Docker Compose deployment

## Load Test Results (AWS EC2 t3.micro)

| Users | Median | p95 | p99 | Failures |
|-------|--------|-----|-----|----------|
| 100   | 33ms   | 160ms | 740ms | 0% |
| 500   | ~30s   | 31s | 31s | 0% |

**Bottleneck at 500 users**: Single vCPU t3.micro saturated. Fix: multiple uvicorn workers + dedicated Redis instance.

## Tech Stack
- **Backend**: Python, FastAPI, Redis, PostgreSQL
- **Algorithms**: Token Bucket (Lua script), Sliding Window (sorted sets)
- **Frontend**: React, Recharts, Vite
- **Infra**: Docker, AWS EC2
- **Load Testing**: Locust

## Running Locally

```bash
# Start infrastructure
docker-compose up -d

# Start backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Start frontend
cd frontend && npm install && npm run dev
```

## API
POST /check      - Check if request is allowed
GET  /rules      - List all rules
POST /rules      - Create a rule
GET  /logs       - View request logs
GET  /health     - Health check
## What I'd Do Differently at Scale

**Multiple uvicorn workers**: Currently running single process. At scale: `uvicorn app.main:app --workers 4` to utilize all CPU cores.

**Dedicated Redis instance**: Redis is on the same box as the app. At scale: AWS ElastiCache (managed Redis) — separate machine, no resource contention.

**Redis Cluster for horizontal scaling**: Single Redis becomes a bottleneck above ~100k RPS. Redis Cluster shards keys across nodes. Rate limit keys shard naturally by user_id.

**Replace polling logs with WebSocket**: Done — dashboard now uses WebSocket for real-time metrics.

**Sliding window memory cost**: Each request stores one sorted set entry. At 1M requests/minute, that's significant memory. Fix: switch high-traffic endpoints to fixed window counter (less accurate but O(1) memory).

**Database connection pooling**: PgBouncer in front of Postgres to handle connection spikes without exhausting the Postgres connection limit.
## Live Demo
Backend: http://3.109.152.24:8000/docs
