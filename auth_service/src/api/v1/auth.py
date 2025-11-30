from fastapi import APIRouter, Depends, HTTPException, status, Response
from src.schemas.auth import RefreshTokenSchema, TokenResponse
from src.core.dependencies import get_current_user, oauth2_scheme
from src.models.entity import User
from src.services.auth import AuthService, get_auth_service
from src.services.user import UserService, get_user_service
from src.schemas.user import UserLogin


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    user_data: UserLogin,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await user_service.get_user_by_login(user_data.login)
    if not user or not user.check_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
        )

    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    access_token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.logout(user=current_user, access_token=access_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    data: RefreshTokenSchema,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    token_response = await auth_service.refresh(data.refresh_token)

    return token_response
