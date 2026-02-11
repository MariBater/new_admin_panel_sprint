from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from auth_service.src.core.config import settings
from auth_service.src.models.entity import User
from auth_service.src.services.auth import AuthService, get_auth_service
from auth_service.src.services.user import UserService, get_user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
) -> User:
    return await auth_service.get_user_from_token(token, user_service)


async def require_superuser(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Superuser privileges required")