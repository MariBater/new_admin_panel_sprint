from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi_sso.sso.yandex import YandexSSO
from fastapi.responses import ORJSONResponse

from auth_service.src.models.entity import User
from auth_service.src.services.auth import AuthService, get_auth_service
from auth_service.src.services.user import UserService, get_user_service
from auth_service.src.core.config import settings


yandex_sso = YandexSSO(
    client_id=settings.YANDEX_CLIENT_ID,
    client_secret=settings.YANDEX_CLIENT_SECRET,
    redirect_uri=settings.YANDEX_REDIRECT_URI,
    allow_insecure_http=True,  # Для локальной разработки по HTTP
)

router = APIRouter(prefix="/oauth/yandex", tags=["social_auth"])


@router.get("/login", summary="Redirect to Yandex for authentication")
async def yandex_login():
    """Перенаправление пользователя на страницу аутентификации Яндекса."""
    return await yandex_sso.get_login_redirect()


@router.get("/callback", summary="Process Yandex authentication callback")
async def yandex_callback(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Обработка ответа от Яндекса после аутентификации пользователя.
    Если пользователь с таким email уже есть, он будет аутентифицирован.
    Если нет — будет создан новый пользователь и затем аутентифицирован.
    """
    try:
        user_info = await yandex_sso.verify_and_process(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify Yandex user: {e}",
        )

    user = await user_service.get_user_by_email(email=user_info.email)
    if not user:
        user = await user_service.create_social_user(
            email=user_info.email,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
        )

    access_token = await auth_service.create_access_token(user)
    refresh_token = await auth_service.create_refresh_token(user)

    user_agent = request.headers.get("user-agent")
    await user_service.login(user_id=user.id, user_agent=user_agent)

    return ORJSONResponse(content={"access_token": access_token, "refresh_token": refresh_token})