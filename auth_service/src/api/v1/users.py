from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import get_current_user, UserPayload
# Эти модели нужно будет создать
from src.models.auth import UserUpdateCredentials 

router = APIRouter()


# ЗАГЛУШКИ СЕРВИСНЫХ ФУНКЦИЙ
# В реальном приложении они будут в src/services/user_service.py и работать с БД
async def update_user_credentials_in_db(login: str, new_login: str | None, new_password_hash: str | None):
    print(f"Pretending to update credentials for {login} in DB.")
    # Логика обновления данных в PostgreSQL
    return {"id": "some-uuid", "login": new_login or login}

async def get_login_history_from_db(login: str):
    print(f"Pretending to fetch login history for {login} from DB.")
    # Логика получения истории из PostgreSQL
    return [
        {"ip_address": "192.168.1.1", "user_agent": "Chrome", "login_at": "2023-10-27T10:00:00Z"},
        {"ip_address": "8.8.8.8", "user_agent": "Firefox", "login_at": "2023-10-26T18:30:00Z"},
    ]
# Конец заглушек


@router.patch("/me/credentials", status_code=status.HTTP_200_OK)
async def update_user_credentials(
    update_data: UserUpdateCredentials,
    current_user: UserPayload = Depends(get_current_user),
):
    if not update_data.login and not update_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update.")
    
    # В реальном приложении хэширование пароля должно быть здесь или в сервисе
    # new_password_hash = get_password_hash(update_data.password) if update_data.password else None
    
    updated_user = await update_user_credentials_in_db(current_user.sub, update_data.login, update_data.password)
    return updated_user


@router.get("/me/login-history", status_code=status.HTTP_200_OK)
async def get_user_login_history(current_user: UserPayload = Depends(get_current_user)):
    history = await get_login_history_from_db(current_user.sub)
    return history