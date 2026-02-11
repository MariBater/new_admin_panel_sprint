from typing import Protocol
from redis.asyncio import Redis
from src.core.config import settings


class AuthRepository(Protocol):

    async def save_refresh_token(self, user_id, refresh_token) -> None: ...
    async def get_refresh_token(self, user_id) -> str | None: ...
    async def delete_refresh_token(self, user_id) -> str | None: ...

    async def save_novalid_access_token(self, user_id, acceess_token) -> None: ...
    async def get_novalid_access_token(self, user_id) -> str | None: ...


class RedisAuthRepository:

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def save_refresh_token(self, user_id, refresh_token) -> None:
        res = await self.redis.setex(
            user_id,
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 60 * 60 * 24,
            refresh_token,
        )

    async def get_refresh_token(self, user_id) -> str | None:
        return await self.redis.get(user_id)

    async def delete_refresh_token(self, user_id) -> str | None:
        return await self.redis.delete(user_id)

    async def save_novalid_access_token(self, user_id, acceess_token) -> None:
        await self.redis.setex(
            f"novalid_{user_id}",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            acceess_token,
        )

    async def get_novalid_access_token(self, user_id) -> str | None:
        return await self.redis.get(
            f"novalid_{user_id}",
        )
