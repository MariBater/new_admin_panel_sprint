from typing import Any

from redis.asyncio import Redis

from .cache_abc import AsyncCache


class RedisCache(AsyncCache):
    """Конкретная реализация кеша на Redis."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Any | None:
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, expire: int):
        await self.redis.set(key, value, ex=expire)
