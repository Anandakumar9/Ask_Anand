"""Redis cache for pre-generated questions and session state.

Gracefully degrades with IN-MEMORY fallback — when Redis is unavailable,
uses a Python dict to cache questions. This ensures pre-generation works
even without Redis (though cache won't survive server restarts).

Enhanced with multi-layer caching:
- Question pool preloading (topic-based)
- User profile stats cache
- LRU question cache
- Connection pooling
- Cache metrics
"""
import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache with max size and item TTL."""

    def __init__(self, max_items: int = 50, default_ttl: int = 3600):
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.max_items = max_items
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item, moving to end (most recently used)."""
        if key not in self.cache:
            self.misses += 1
            return None

        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            self.misses += 1
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set item with TTL, evicting oldest if max_items reached."""
        expiry = time.time() + (ttl or self.default_ttl)

        if key in self.cache:
            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_items:
                # Evict oldest item
                self.cache.popitem(last=False)
            self.cache[key] = (value, expiry)

    def delete(self, key: str):
        """Remove item from cache."""
        self.cache.pop(key, None)

    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class RedisCache:
    """Async Redis cache with multi-layer caching and graceful fallback."""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._available = False

        # In-memory fallback: {key: (data, expiry_timestamp)}
        self._memory_cache: dict[str, tuple[str, float]] = {}

        # Multi-layer caches
        self._question_pool_cache: dict[int, tuple[list[dict], float]] = {}  # topic_id -> (questions, expiry)
        self._profile_cache = LRUCache(max_items=100, default_ttl=300)  # 5 min TTL
        self._lru_question_cache = LRUCache(max_items=50, default_ttl=86400)  # 24 hr TTL

        # Metrics
        self._metrics = {
            'redis_hits': 0,
            'redis_misses': 0,
            'memory_hits': 0,
            'memory_misses': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'errors': 0,
        }

        # Background task for cleanup
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Connect to Redis with connection pooling."""
        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
            )
            self._redis = aioredis.Redis(connection_pool=self._pool)

            # Test connection with retry
            for attempt in range(3):
                try:
                    await self._redis.ping()
                    self._available = True
                    logger.info("[OK] Redis cache connected with connection pooling")
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        except Exception as e:
            logger.warning(
                f"[WARNING] Redis not available: {e}. "
                f"Using IN-MEMORY cache fallback (non-persistent)."
            )
            self._available = False

    async def close(self):
        """Close Redis connection and cleanup tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()

    async def health_check(self) -> dict[str, Any]:
        """Check Redis health and return status."""
        if not self._available:
            return {
                'status': 'degraded',
                'backend': 'memory',
                'message': 'Using in-memory fallback'
            }

        try:
            latency_start = time.time()
            await self._redis.ping()
            latency = (time.time() - latency_start) * 1000  # ms

            info = await self._redis.info('stats')

            return {
                'status': 'healthy',
                'backend': 'redis',
                'latency_ms': round(latency, 2),
                'total_connections_received': info.get('total_connections_received', 0),
                'connected_clients': info.get('connected_clients', 0),
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'backend': 'redis',
                'error': str(e)
            }

    @property
    def available(self) -> bool:
        return self._available

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        total_requests = (
            self._metrics['redis_hits'] + self._metrics['redis_misses'] +
            self._metrics['memory_hits'] + self._metrics['memory_misses']
        )
        hit_rate = 0.0
        if total_requests > 0:
            total_hits = self._metrics['redis_hits'] + self._metrics['memory_hits'] + self._metrics['pool_hits']
            hit_rate = round((total_hits / total_requests) * 100, 2)

        return {
            **self._metrics,
            'total_requests': total_requests,
            'hit_rate_percentage': hit_rate,
            'profile_cache_size': len(self._profile_cache.cache),
            'lru_question_cache_size': len(self._lru_question_cache.cache),
            'question_pool_cache_size': len(self._question_pool_cache),
            'memory_cache_size': len(self._memory_cache),
            'profile_cache_hit_rate': round(
                (self._profile_cache.hits / max(1, self._profile_cache.hits + self._profile_cache.misses)) * 100, 2
            ),
            'lru_cache_hit_rate': round(
                (self._lru_question_cache.hits / max(1, self._lru_question_cache.hits + self._lru_question_cache.misses)) * 100, 2
            ),
        }

    async def _periodic_cleanup(self):
        """Background task to clean up expired cache entries every 5 minutes."""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                self._memory_cleanup()
                self._cleanup_question_pool()
                logger.debug("🧹 Periodic cache cleanup completed")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    def _cleanup_question_pool(self):
        """Remove expired entries from question pool cache."""
        now = time.time()
        expired = [topic_id for topic_id, (_, exp) in self._question_pool_cache.items() if now > exp]
        for topic_id in expired:
            del self._question_pool_cache[topic_id]
        if expired:
            logger.debug("[CLEANUP] Cleaned {len(expired)} expired question pool entries")

    # ── In-memory cache helpers ──────────────────────────────

    def _memory_set(self, key: str, value: str, ttl: int):
        """Store in memory with TTL."""
        expiry = time.time() + ttl
        self._memory_cache[key] = (value, expiry)
        logger.debug(f"[CACHE] Memory cache SET: {key} (TTL={ttl}s)")

    def _memory_get(self, key: str) -> Optional[str]:
        """Get from memory, respecting TTL."""
        if key not in self._memory_cache:
            self._metrics['memory_misses'] += 1
            return None
        value, expiry = self._memory_cache[key]
        if time.time() > expiry:
            # Expired
            del self._memory_cache[key]
            logger.debug(f"⏰ Memory cache EXPIRED: {key}")
            self._metrics['memory_misses'] += 1
            return None
        logger.debug(f"[HIT] Memory cache HIT: {key}")
        self._metrics['memory_hits'] += 1
        return value

    def _memory_delete(self, key: str):
        """Delete from memory."""
        self._memory_cache.pop(key, None)
        logger.debug(f"[DELETE] Memory cache DELETE: {key}")

    def _memory_cleanup(self):
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, (_, exp) in self._memory_cache.items() if now > exp]
        for k in expired:
            del self._memory_cache[k]
        if expired:
            logger.debug("[CLEANUP] Cleaned {len(expired)} expired cache entries")

    # ── Multi-layer cache methods ─────────────────────────────

    async def cache_question_pool(self, topic_id: int, questions: list[dict], ttl: int = 1800):
        """Cache all questions for a topic (refreshed periodically)."""
        expiry = time.time() + ttl
        self._question_pool_cache[topic_id] = (questions, expiry)
        logger.info(f"[CACHE] Cached question pool for topic={topic_id} ({len(questions)} questions)")

    def get_question_pool(self, topic_id: int) -> Optional[list[dict]]:
        """Get cached question pool for topic."""
        if topic_id not in self._question_pool_cache:
            self._metrics['pool_misses'] += 1
            return None

        questions, expiry = self._question_pool_cache[topic_id]
        if time.time() > expiry:
            del self._question_pool_cache[topic_id]
            self._metrics['pool_misses'] += 1
            return None

        self._metrics['pool_hits'] += 1
        return questions

    def invalidate_question_pool(self, topic_id: int):
        """Invalidate question pool cache for topic."""
        self._question_pool_cache.pop(topic_id, None)
        logger.info(f"[DELETE] Invalidated question pool for topic={topic_id}")

    async def cache_profile_stats(self, user_id: int, stats: dict):
        """Cache user profile stats (5 min TTL)."""
        key = f"profile:{user_id}"
        self._profile_cache.set(key, stats)
        logger.debug(f"[CACHE] Cached profile stats for user={user_id}")

    def get_profile_stats(self, user_id: int) -> Optional[dict]:
        """Get cached profile stats."""
        key = f"profile:{user_id}"
        return self._profile_cache.get(key)

    def invalidate_profile_stats(self, user_id: int):
        """Invalidate profile stats cache."""
        key = f"profile:{user_id}"
        self._profile_cache.delete(key)
        logger.debug(f"[DELETE] Invalidated profile stats for user={user_id}")

    async def cache_question_set(self, topic_id: int, user_id: int, questions: list[dict]):
        """Cache question set in LRU cache (24 hr TTL)."""
        key = f"qset:t{topic_id}:u{user_id}"
        self._lru_question_cache.set(key, questions)
        logger.debug(f"[CACHE] Cached question set for topic={topic_id} user={user_id}")

    def get_question_set(self, topic_id: int, user_id: int) -> Optional[list[dict]]:
        """Get cached question set from LRU cache."""
        key = f"qset:t{topic_id}:u{user_id}"
        return self._lru_question_cache.get(key)

    # ── Pre-generated question cache ──────────────────────────

    def _key(self, topic_id: int, user_id: int) -> str:
        return f"pregen:t{topic_id}:u{user_id}"

    async def cache_pregenerated_questions(
        self, topic_id: int, user_id: int, questions: list[dict], ttl: int = 3600
    ):
        """Store pre-generated questions (consumed once on test start)."""
        data = json.dumps(questions)
        key = self._key(topic_id, user_id)

        if self._available:
            # Use Redis
            try:
                await self._redis.setex(key, ttl, data)
                logger.info(
                    f"[OK] Redis cached {len(questions)} questions "
                    f"topic={topic_id} user={user_id}"
                )
                return
            except Exception as e:
                logger.warning(f"Redis write failed: {e}, falling back to memory")
                self._metrics['errors'] += 1

        # Fallback to memory
        self._memory_set(key, data, ttl)
        logger.info(
            f"📦 Memory cached {len(questions)} questions "
            f"topic={topic_id} user={user_id}"
        )

    async def get_pregenerated_questions(
        self, topic_id: int, user_id: int
    ) -> Optional[list[dict]]:
        """Get pre-generated questions (persistent until TTL expires)."""
        self._memory_cleanup()  # Clean expired entries
        key = self._key(topic_id, user_id)

        if self._available:
            # Try Redis first
            try:
                data = await self._redis.get(key)
                if data:
                    questions = json.loads(data)
                    logger.info(
                        f"[HIT] Redis HIT: {len(questions)} questions "
                        f"topic={topic_id} user={user_id}"
                    )
                    self._metrics['redis_hits'] += 1
                    return questions
                else:
                    self._metrics['redis_misses'] += 1
            except Exception as e:
                logger.warning(f"Redis read failed: {e}, trying memory")
                self._metrics['errors'] += 1

        # Try memory fallback
        data = self._memory_get(key)
        if data:
            questions = json.loads(data)
            logger.info(
                f"📦 Memory HIT: {len(questions)} questions "
                f"topic={topic_id} user={user_id}"
            )
            return questions

        return None

    # ── Pre-generation status ─────────────────────────────────

    async def set_pregen_status(self, topic_id: int, user_id: int, status: str):
        key = f"pregen_st:t{topic_id}:u{user_id}"
        if self._available:
            try:
                await self._redis.setex(key, 600, status)
                return
            except Exception as e:
                logger.debug(f"Redis setex failed for pregen status: {e}")
        # Memory fallback
        self._memory_set(key, status, 600)

    async def get_pregen_status(self, topic_id: int, user_id: int) -> Optional[str]:
        key = f"pregen_st:t{topic_id}:u{user_id}"
        if self._available:
            try:
                return await self._redis.get(key)
            except Exception:
                pass
        # Memory fallback
        return self._memory_get(key)


# Singleton
cache = RedisCache()
