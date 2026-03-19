from prometheus_fastapi_instrumentator import Instrumentator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import router as api_router
from app.core.config import settings
from app.core.database import engine
from app.workers.escalation_worker import run_escalations
from app.workers.sla_worker import check_sla_breaches

# Single scheduler instance
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────
    print(f"Starting {settings.PROJECT_NAME}...")

    # Verify database connection
    async with engine.connect() as conn:
        print("Database connection OK")

    # Verify Redis connection
    redis = aioredis.from_url(settings.REDIS_URL)
    result = await redis.ping()  # pyright: ignore[reportGeneralTypeIssues]
    assert result is True, "Redis ping failed"
    await redis.aclose()
    print("Redis connection OK")

    # Start background workers
    scheduler.add_job(
        check_sla_breaches,
        trigger="interval",
        seconds=60,
        id="sla_checker",
        replace_existing=True,
    )
    scheduler.add_job(
        run_escalations,
        trigger="interval",
        seconds=60,
        id="escalation_runner",
        replace_existing=True,
    )
    scheduler.start()
    print("Background workers started (SLA checker + Escalation runner)")

    yield  # app is running

    # ── Shutdown ───────────────────────────────────────────
    print("Shutting down...")
    scheduler.shutdown(wait=False)
    await engine.dispose()
    print("Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)

# CORS
if settings.ENVIRONMENT == "local":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME}
