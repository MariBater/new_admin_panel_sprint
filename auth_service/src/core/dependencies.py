from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel

from src.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UserPayload(BaseModel):
    sub: str  # 'sub' is standard for subject, which is our user identifier (e.g., login or id)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
        
        # Здесь можно добавить проверку, что пользователь все еще существует в БД
        # user = await get_user_by_login(login)
        # if user is None:
        #     raise credentials_exception
            
        return UserPayload(sub=login)
    except JWTError:
        raise credentials_exception