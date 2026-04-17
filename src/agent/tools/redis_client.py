"""
Redis client wrapper.

Uses FakeRedis in-memory store by default.
Set REDIS_URL env var to connect to a real Redis instance.
"""

from __future__ import annotations

import json
import os
from typing import Any


class FakeRedis:
    """In-memory Redis substitute for demo / testing."""

    def __init__(self):
        self._store: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def expire(self, key: str, seconds: int) -> None:
        pass  # TTL is a no-op for the in-memory store

    def keys(self, pattern: str = "*") -> list[str]:
        if pattern == "*":
            return list(self._store.keys())
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]


class RedisClient:
    """
    Unified Redis interface.

    - If REDIS_URL is set, connects to real Redis.
    - Otherwise falls back to FakeRedis for local demo.
    """

    def __init__(self):
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            import redis as redis_lib
            self._client = redis_lib.Redis.from_url(redis_url, decode_responses=True)
        else:
            self._client = FakeRedis()

    def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized = json.dumps(value)
        self._client.set(key, serialized, ex=ttl)

    def get_json(self, key: str) -> Any | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def expire(self, key: str, seconds: int) -> None:
        self._client.expire(key, seconds)

    def keys(self, pattern: str = "*") -> list[str]:
        return self._client.keys(pattern)


# ── Singleton ──
_instance: RedisClient | None = None


def get_redis_client() -> RedisClient:
    global _instance
    if _instance is None:
        _instance = RedisClient()
    return _instance
