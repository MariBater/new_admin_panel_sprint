from enum import Enum
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from api_clients.auth_client import AuthClient
from schemas.user import User
from core.config import settings
from core.logger import app_logger


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"
    PREMIUM_USER = "premium_user"


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def validate_role(
    token: str = Depends(oauth2_scheme),
    roles: list = [],
    use_auth_service: bool = False,
    use_graceful_degradation: bool = True,
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
        app_logger.error(payload)
        user_id: str | None = payload.get("user_id")
        login: str | None = payload.get("login")
        payload_roles: str | None = payload.get('roles')

        if user_id is None or login is None or payload_roles is None:
            raise credentials_exception

        app_logger.error(use_auth_service)
        if use_auth_service:
            authClient = AuthClient()
            try:
                for role in payload_roles.split(','):
                    valid_role = await authClient.check_role(
                        access_token=token,
                        user_id=user_id,
                        role=role,
                    )
                    app_logger.error("valid_role-" + str(valid_role.text))
                    if not valid_role.text:
                        raise credentials_exception
            except Exception as e:
                app_logger.error("e-" + str(e))
                if not use_graceful_degradation:
                    raise credentials_exception

        valid_role = False
        for item in payload_roles.split(','):
            for role in roles:
                if item == role.value:
                    valid_role = True

        if not valid_role:
            raise credentials_exception

        return User(id=user_id, login=login, roles=payload_roles)
    except Exception as e:
        raise credentials_exception
    except JWTError:
        raise credentials_exception


def require_roles(
    roles: list[str],
    use_auth_service: bool = False,
    use_graceful_degradation: bool = True,
):
    async def dependency(
        token: str = Depends(oauth2_scheme),
    ) -> User:
        return await validate_role(
            token=token,
            roles=roles,
            use_auth_service=use_auth_service,
            use_graceful_degradation=use_graceful_degradation,
        )

    return dependency
