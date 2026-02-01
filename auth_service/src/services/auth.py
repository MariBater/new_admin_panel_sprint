from datetime import datetime, timedelta, timezone
from typing import Any
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from redis.asyncio import Redis

from src.core.config import settings
from src.db.redis import get_redis
from src.models.entity import User
from src.services.user import UserService, get_user_service


class AuthService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def create_access_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {"sub": str(user.id), "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    async def create_refresh_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode = {"sub": str(user.id), "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        await self.redis.set(f"refresh_token:{user.id}", encoded_jwt, ex=expire - datetime.now(timezone.utc))
        return encoded_jwt

    async def get_user_from_token(
        self, token: str, user_service: UserService
    ) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await user_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception
        return user

    async def logout(self, user: User, access_token: str):
        # Просто для примера, можно добавить токен в черный список
        await self.redis.delete(f"refresh_token:{user.id}")

    async def refresh(self, refresh_token: str):
        # В реальном приложении здесь будет более сложная логика
        return {"access_token": "new_access", "refresh_token": "new_refresh"}


@lru_cache()
def get_auth_service(redis: Redis = Depends(get_redis)) -> AuthService:
    return AuthService(redis)