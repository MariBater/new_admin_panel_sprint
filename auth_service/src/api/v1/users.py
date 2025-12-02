from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, status
from src.services.role import RoleService, get_role_service
from src.models.entity import User
from src.services.user import UserService, get_user_service
from src.core.dependencies import get_current_user
from src.schemas.user import UserRegister, UserUpdateCredentials


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    user_service: UserService = Depends(get_user_service),
    role_service: RoleService = Depends(get_role_service),
) -> bool:
    user = await user_service.get_user_by_login(login=user_data.login)
    if user:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="User already created",
        )
    role = await role_service.get_by_name('user')
    await user_service.create_user(user_data, role)

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

    updated_user = await user_service.update_user_credentials(
        user_id=current_user.id, update_data=update_data
    )

    return {"user_id": updated_user.id, 'login': updated_user.login}


@router.get("/me/login-history", status_code=status.HTTP_200_OK)
async def get_user_login_history(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    user_history_list = await user_service.get_login_history(user_id=current_user.id)
    return [
        {"user_agent": h.user_agent, 'login_at': h.auth_date} for h in user_history_list
    ]
