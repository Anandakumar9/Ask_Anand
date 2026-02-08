"""Redis cache for pre-generated questions and session state.

Gracefully degrades — the app works without Redis, just slower
(no pre-generation cache, no instant test starts).
"""
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis cache with graceful degradation."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._available = False

    async def initialize(self):
        """Connect to Redis."""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self._redis.ping()
            self._available = True
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Running without cache.")
            self._available = False

    async def close(self):
        if self._redis:
            await self._redis.close()

    @property
    def available(self) -> bool:
        return self._available

    # ── Pre-generated question cache ──────────────────────────

    def _key(self, topic_id: int, user_id: int) -> str:
        return f"pregen:t{topic_id}:u{user_id}"

    async def cache_pregenerated_questions(
        self, topic_id: int, user_id: int, questions: list[dict], ttl: int = 3600
    ):
        """Store pre-generated questions (consumed once on test start)."""
        if not self._available:
            return
        try:
            await self._redis.setex(
                self._key(topic_id, user_id), ttl, json.dumps(questions)
            )
            logger.info(f"Cached {len(questions)} questions topic={topic_id} user={user_id}")
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def get_pregenerated_questions(
        self, topic_id: int, user_id: int
    ) -> Optional[list[dict]]:
        """Pop pre-generated questions (one-time use)."""
        if not self._available:
            return None
        try:
            key = self._key(topic_id, user_id)
            data = await self._redis.get(key)
            if data:
                await self._redis.delete(key)
                questions = json.loads(data)
                logger.info(f"Cache HIT: {len(questions)} questions for topic={topic_id}")
                return questions
            return None
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
            return None

    # ── Pre-generation status ─────────────────────────────────

    async def set_pregen_status(self, topic_id: int, user_id: int, status: str):
        if not self._available:
            return
        try:
            await self._redis.setex(f"pregen_st:t{topic_id}:u{user_id}", 600, status)
        except Exception:
            pass

    async def get_pregen_status(self, topic_id: int, user_id: int) -> Optional[str]:
        if not self._available:
            return None
        try:
            return await self._redis.get(f"pregen_st:t{topic_id}:u{user_id}")
        except Exception:
            return None


# Singleton
cache = RedisCache()
