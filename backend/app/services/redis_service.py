import redis.asyncio as aioredis

from app.core.config import settings

# Deduplication window — if same fingerprint seen within
# this many seconds, suppress the alert
DEDUP_TTL_SECONDS = 600  # 10 minutes


class RedisService:
    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def get_client(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def is_duplicate(self, fingerprint: str, team_id: int) -> bool:
        """
        Check if this fingerprint was seen recently.
        Returns True if duplicate (should suppress), False if new.

        Uses Redis SET NX (set if not exists) with TTL:
        - First time seen → sets key, returns False (not duplicate)
        - Seen again within TTL → key exists, returns True (duplicate)
        """
        redis = await self.get_client()
        key = f"alert:dedup:{team_id}:{fingerprint}"

        # SET key value NX EX ttl
        # NX = only set if not exists
        # Returns True if set (new), None if already existed (duplicate)
        result = await redis.set(key, "1", nx=True, ex=DEDUP_TTL_SECONDS)
        return result is None  # None means key already existed = duplicate

    async def clear_fingerprint(self, fingerprint: str, team_id: int) -> None:
        """Manually clear a fingerprint — useful for testing."""
        redis = await self.get_client()
        key = f"alert:dedup:{team_id}:{fingerprint}"
        await redis.delete(key)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None


# Single instance — imported by services that need it
redis_service = RedisService()
