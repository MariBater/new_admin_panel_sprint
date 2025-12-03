from datetime import datetime, timedelta
from functools import lru_cache
from http import HTTPStatus
from uuid import UUID
from fastapi import Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import TokenResponse
from src.repositories.user_repository import (
    PgUserRepository,
    UserRepository,
)
from src.db.redis import get_redis
from src.models.entity import User
from src.repositories.auth_repository import AuthRepository, RedisAuthRepository
from src.db.postgres import get_session
from src.core.config import settings
from jose import ExpiredSignatureError, JWTError, jwt
from src.core.logger import app_logger


class AuthService:

    def __init__(
        self,
        session: AsyncSession,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
    ) -> None:
        self.session = session
        self.auth_repo = auth_repo
        self.user_repo = user_repo

    async def create_access_token(self, user: User):
        to_encode = {'user_id': str(user.id), 'login': user.login}.copy()

        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def create_refresh_token(self, user: User):
        to_encode = {'user_id': str(user.id), 'login': user.login}.copy()

        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        await self.auth_repo.save_refresh_token(str(user.id), encoded_jwt)

        return encoded_jwt

    async def logout(self, user: User, access_token: str):
        try:
            await self.auth_repo.save_novalid_access_token(
                str(user.id), acceess_token=access_token
            )
            await self.auth_repo.delete_refresh_token(str(user.id))
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while logout",
            )

    async def novalid_access_token(self, user_id: UUID, access_token: str):
        try:
            token = await self.auth_repo.get_novalid_access_token(str(user_id))
            if token and token == access_token:
                return True

            return False
        except Exception as e:
            app_logger.error(e)
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Internal server error while logout",
            )

    async def refresh(self, token: str):
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )

            user_id = payload.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            user = await self.user_repo.get(user_id=UUID(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            saved_token = await self.auth_repo.get_refresh_token(user_id)

            if token != saved_token:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            access_token = await self.create_access_token(user)
            refresh_token = await self.create_refresh_token(user)

            return TokenResponse(access_token=access_token, refresh_token=refresh_token)

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        except HTTPException:
            raise

        except Exception as e:
            app_logger.exception(e)
            raise HTTPException(
                status_code=500, detail="Internal server error while refresh_token"
            )


@lru_cache()
def get_auth_service(
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> AuthService:
    auth_repo = RedisAuthRepository(redis=redis)
    user_repo = PgUserRepository(session=session)
    return AuthService(session=session, auth_repo=auth_repo, user_repo=user_repo)
