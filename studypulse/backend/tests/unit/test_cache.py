"""Unit tests for cache system (Redis + in-memory fallback)."""
import asyncio
import time

import pytest

from app.core.cache import LRUCache, RedisCache


class TestLRUCache:
    """Test in-memory LRU cache implementation."""

    def test_lru_cache_basic_operations(self):
        """Test basic get/set operations."""
        cache = LRUCache(max_items=3, default_ttl=3600)

        # Set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Cache miss
        assert cache.get("nonexistent") is None

    def test_lru_cache_expiration(self):
        """Test TTL expiration."""
        cache = LRUCache(max_items=5, default_ttl=1)  # 1 second TTL

        cache.set("key1", "value1", ttl=1)

        # Should exist immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_lru_cache_max_items_eviction(self):
        """Test eviction when max items is reached."""
        cache = LRUCache(max_items=3, default_ttl=3600)

        # Add 3 items (at capacity)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should exist
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

        # Add 4th item (should evict oldest)
        cache.set("key4", "value4")

        # key1 (oldest) should be evicted
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_cache_access_order(self):
        """Test LRU eviction based on access order."""
        cache = LRUCache(max_items=3, default_ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 (makes it most recently used)
        cache.get("key1")

        # Add key4 (should evict key2, not key1)
        cache.set("key4", "value4")

        # key2 should be evicted (least recently used)
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_cache_update_existing(self):
        """Test updating existing key."""
        cache = LRUCache(max_items=3, default_ttl=3600)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Update same key
        cache.set("key1", "new_value")
        assert cache.get("key1") == "new_value"

    def test_lru_cache_delete(self):
        """Test explicit deletion."""
        cache = LRUCache(max_items=3, default_ttl=3600)

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        cache.delete("key1")
        assert cache.get("key1") is None

    def test_lru_cache_clear(self):
        """Test clearing entire cache."""
        cache = LRUCache(max_items=5, default_ttl=3600)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert len(cache.cache) == 0

    def test_lru_cache_metrics(self):
        """Test hit/miss metrics tracking."""
        cache = LRUCache(max_items=5, default_ttl=3600)

        cache.set("key1", "value1")

        # Hits
        cache.get("key1")
        cache.get("key1")

        # Misses
        cache.get("key2")
        cache.get("key3")

        assert cache.hits == 2
        assert cache.misses == 2


@pytest.mark.asyncio
class TestRedisCache:
    """Test Redis cache with in-memory fallback."""

    async def test_redis_initialization_fallback(self):
        """Test cache initializes with in-memory fallback when Redis unavailable."""
        cache = RedisCache()

        # Initialize (should fall back to memory if Redis unavailable)
        await cache.initialize()

        # Should always initialize successfully (fallback to memory)
        assert cache is not None

        await cache.close()

    async def test_memory_cache_set_get(self):
        """Test in-memory cache set/get operations."""
        cache = RedisCache()
        await cache.initialize()

        # Use memory cache directly
        cache._memory_set("test_key", "test_value", ttl=3600)
        value = cache._memory_get("test_key")

        assert value == "test_value"

        await cache.close()

    async def test_memory_cache_expiration(self):
        """Test in-memory cache TTL expiration."""
        cache = RedisCache()
        await cache.initialize()

        # Set with 1 second TTL
        cache._memory_set("key1", "value1", ttl=1)

        # Should exist immediately
        assert cache._memory_get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert cache._memory_get("key1") is None

        await cache.close()

    async def test_memory_cache_delete(self):
        """Test in-memory cache deletion."""
        cache = RedisCache()
        await cache.initialize()

        cache._memory_set("key1", "value1", ttl=3600)
        assert cache._memory_get("key1") == "value1"

        cache._memory_delete("key1")
        assert cache._memory_get("key1") is None

        await cache.close()

    async def test_memory_cleanup(self):
        """Test periodic cleanup of expired entries."""
        cache = RedisCache()
        await cache.initialize()

        # Add entries with short TTL
        cache._memory_set("key1", "value1", ttl=1)
        cache._memory_set("key2", "value2", ttl=1)
        cache._memory_set("key3", "value3", ttl=3600)

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Trigger cleanup
        cache._memory_cleanup()

        # Expired entries should be removed
        assert cache._memory_get("key1") is None
        assert cache._memory_get("key2") is None
        assert cache._memory_get("key3") == "value3"

        await cache.close()

    async def test_question_pool_cache(self):
        """Test question pool caching."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 123
        questions = [
            {"id": 1, "text": "Question 1"},
            {"id": 2, "text": "Question 2"},
        ]

        # Cache question pool
        await cache.cache_question_pool(topic_id, questions, ttl=3600)

        # Retrieve from cache
        cached = cache.get_question_pool(topic_id)

        assert cached is not None
        assert len(cached) == 2
        assert cached[0]["id"] == 1

        await cache.close()

    async def test_question_pool_expiration(self):
        """Test question pool cache expiration."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 456
        questions = [{"id": 1, "text": "Question 1"}]

        # Cache with 1 second TTL
        await cache.cache_question_pool(topic_id, questions, ttl=1)

        # Should exist immediately
        assert cache.get_question_pool(topic_id) is not None

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert cache.get_question_pool(topic_id) is None

        await cache.close()

    async def test_question_pool_invalidation(self):
        """Test manual invalidation of question pool."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 789
        questions = [{"id": 1, "text": "Question 1"}]

        await cache.cache_question_pool(topic_id, questions)
        assert cache.get_question_pool(topic_id) is not None

        # Invalidate
        cache.invalidate_question_pool(topic_id)

        assert cache.get_question_pool(topic_id) is None

        await cache.close()

    async def test_profile_stats_cache(self):
        """Test profile stats caching (LRU cache)."""
        cache = RedisCache()
        await cache.initialize()

        user_id = 100
        stats = {
            "total_stars": 50,
            "total_tests": 10,
            "accuracy": 85.5
        }

        # Cache profile stats
        await cache.cache_profile_stats(user_id, stats)

        # Retrieve from cache
        cached_stats = cache.get_profile_stats(user_id)

        assert cached_stats is not None
        assert cached_stats["total_stars"] == 50
        assert cached_stats["accuracy"] == 85.5

        await cache.close()

    async def test_profile_stats_invalidation(self):
        """Test profile stats cache invalidation."""
        cache = RedisCache()
        await cache.initialize()

        user_id = 200
        stats = {"total_stars": 30}

        await cache.cache_profile_stats(user_id, stats)
        assert cache.get_profile_stats(user_id) is not None

        # Invalidate
        cache.invalidate_profile_stats(user_id)

        assert cache.get_profile_stats(user_id) is None

        await cache.close()

    async def test_question_set_cache(self):
        """Test question set caching (LRU cache)."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 1
        user_id = 100
        questions = [
            {"id": 1, "text": "Question 1"},
            {"id": 2, "text": "Question 2"},
        ]

        # Cache question set
        await cache.cache_question_set(topic_id, user_id, questions)

        # Retrieve from cache
        cached = cache.get_question_set(topic_id, user_id)

        assert cached is not None
        assert len(cached) == 2

        await cache.close()

    async def test_pregenerated_questions_cache(self):
        """Test pre-generated questions caching."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 10
        user_id = 500
        questions = [
            {"id": 1, "text": "Question 1", "options": {}},
        ]

        # Cache pre-generated questions
        await cache.cache_pregenerated_questions(topic_id, user_id, questions, ttl=3600)

        # Retrieve from cache
        cached = await cache.get_pregenerated_questions(topic_id, user_id)

        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["id"] == 1

        await cache.close()

    async def test_pregen_status(self):
        """Test pre-generation status tracking."""
        cache = RedisCache()
        await cache.initialize()

        topic_id = 50
        user_id = 600

        # Set status
        await cache.set_pregen_status(topic_id, user_id, "generating")

        # Get status
        status = await cache.get_pregen_status(topic_id, user_id)

        assert status == "generating"

        # Update status
        await cache.set_pregen_status(topic_id, user_id, "ready")
        status = await cache.get_pregen_status(topic_id, user_id)

        assert status == "ready"

        await cache.close()

    async def test_cache_metrics(self):
        """Test cache metrics tracking."""
        cache = RedisCache()
        await cache.initialize()

        # Perform some cache operations
        cache._memory_set("key1", "value1", ttl=3600)
        cache._memory_get("key1")  # Hit
        cache._memory_get("key2")  # Miss

        metrics = cache.get_metrics()

        assert "total_requests" in metrics
        assert "hit_rate_percentage" in metrics
        assert "memory_cache_size" in metrics

        await cache.close()

    async def test_health_check_memory_fallback(self):
        """Test health check when using memory fallback."""
        cache = RedisCache()
        await cache.initialize()

        health = await cache.health_check()

        assert "status" in health
        assert "backend" in health

        # Should be either 'healthy' (Redis) or 'degraded' (memory)
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

        await cache.close()
