from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.exc import IntegrityError

from auth_service.src.core.dependencies import get_current_user, require_superuser
from auth_service.src.core.tracing import traced
from auth_service.src.models.entity import User
from auth_service.src.schemas.role import RoleName, RoleSchema, RoleUserSchema
from auth_service.src.services.role import RoleService, get_role_service
from opentelemetry import trace

router = APIRouter()


@traced("api_get_all_roles")
@router.get('/')
async def get_all(
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> list[RoleSchema]:
    role_list = await role_service.get_all()
    return [RoleSchema(id=role.id, name=role.name) for role in role_list]


@traced("api_create_role")
@router.post('/', status_code=HTTPStatus.CREATED)
async def create(
    role_data: RoleName,
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> RoleSchema:
    try:
        role = await role_service.create(name=role_data.name)
        return RoleSchema(id=role.id, name=role.name)
    except IntegrityError:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Role with this name already exists',
        )


@traced("api_update_role")
@router.put('/{role_id}')
async def update(
    role_id: UUID,
    role_data: RoleName,
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> RoleSchema:
    role = await role_service.update(role_id=role_id, name=role_data.name)
    if not role:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Role not found')
    return RoleSchema(id=role.id, name=role.name)


@traced("api_delete_role")
@router.delete('/{role_id}', status_code=HTTPStatus.OK)
async def delete(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> bool:
    deleted = await role_service.delete(role_id=role_id)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Role not found')
    return deleted


@traced("api_set_role")
@router.post('/set', status_code=HTTPStatus.OK)
async def set_role(
    user_id: UUID = Body(),
    role_name: str = Body(),
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> bool:
    success = await role_service.set_role(
        RoleUserSchema(user_id=user_id, role_name=role_name)
    )
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="User or Role not found"
        )
    return success


@traced("api_revoke_role")
@router.post('/revoke', status_code=HTTPStatus.OK)
async def revoke_role(
    user_id: UUID = Body(),
    role_name: str = Body(),
    role_service: RoleService = Depends(get_role_service),
    super_user=Depends(require_superuser),
) -> bool:
    success = await role_service.revoke_role(
        RoleUserSchema(user_id=user_id, role_name=role_name)
    )
    if not success:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User or Role not found, or role not assigned",
        )
    return success


@traced("api_check_role")
@router.post('/check')
async def check_role(
    user_id: UUID = Body(),
    role_name: str = Body(),
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(get_current_user),
) -> bool:
    has_role = await role_service.check_role(
        RoleUserSchema(user_id=user_id, role_name=role_name)
    )
    return has_role
