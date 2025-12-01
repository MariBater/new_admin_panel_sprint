from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from src.services.auth import AuthService, get_auth_service
from src.models.entity import User
from src.services.user import UserService, get_user_service
from src.core.config import settings
from src.core.logger import app_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
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
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

        if await auth_service.novalid_access_token(user_id=user_id, access_token=token):
            raise credentials_exception

        user = await user_service.get_user(UUID(user_id))
        if user is None:
            raise credentials_exception

        return user
    except Exception as e:
        app_logger.error(e)
        raise credentials_exception
    except JWTError:
        raise credentials_exception
