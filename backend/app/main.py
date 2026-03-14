from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────
    print(f"Starting {settings.PROJECT_NAME}...")

    # Verify database connection
    async with engine.connect() as conn:
        print("Database connection OK")

    # Verify Redis connection
    redis = aioredis.from_url(settings.REDIS_URL)
    await redis.ping()  # type: ignore[awaitable-return-value]
    await redis.aclose()
    print("Redis connection OK")

    yield  # app is running

    # ── Shutdown ───────────────────────────────────────────
    print("Shutting down...")
    await engine.dispose()
    print("Database connections closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS — allows the React frontend to talk to this backend
if settings.ENVIRONMENT == "local":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Health check — useful for Docker healthcheck and deployment platforms
@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME}
