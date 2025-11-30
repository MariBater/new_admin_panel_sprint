from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, status
from src.models.entity import User
from src.services.user import UserService, get_user_service
from src.core.dependencies import get_current_user
from src.schemas.user import UserRegister, UserUpdateCredentials

router = APIRouter()


async def update_user_credentials_in_db(
    login: str, new_login: str | None, new_password_hash: str | None
):
    print(f"Pretending to update credentials for {login} in DB.")
    # Логика обновления данных в PostgreSQL
    return {"id": "some-uuid", "login": new_login or login}


async def get_login_history_from_db(login: str):
    print(f"Pretending to fetch login history for {login} from DB.")
    # Логика получения истории из PostgreSQL
    return [
        {
            "ip_address": "192.168.1.1",
            "user_agent": "Chrome",
            "login_at": "2023-10-27T10:00:00Z",
        },
        {
            "ip_address": "8.8.8.8",
            "user_agent": "Firefox",
            "login_at": "2023-10-26T18:30:00Z",
        },
    ]


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    user_service: UserService = Depends(get_user_service),
) -> bool:
    user = await user_service.get_user_by_login(login=user_data.login)
    if user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="User already created",
        )
    await user_service.create_user(user_data)

    return True


@router.post("/me/credentials", status_code=status.HTTP_200_OK)
async def update_user_credentials(
    update_data: UserUpdateCredentials,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    if not update_data.login and not update_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update."
        )

    await user_service.update_user_credentials(update_data)
    # updated_user = await update_user_credentials_in_db(
    #     current_user.sub, update_data.login, update_data.password
    # )
    # return updated_user


@router.get("/me/login-history", status_code=status.HTTP_200_OK)
async def get_user_login_history(current_user: User = Depends(get_current_user)):
    history = await get_login_history_from_db(current_user.sub)
    return history