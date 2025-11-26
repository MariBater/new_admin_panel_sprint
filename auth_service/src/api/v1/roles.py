from http import HTTPStatus
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException

from src.schemas.role import RoleName, RoleSchema
from src.services.role import RoleService, get_role_service


router = APIRouter()


@router.get('/')
async def get_all(
    role_service: RoleService = Depends(get_role_service),
) -> list[RoleSchema]:
    role_list = await role_service.get_all()
    return [RoleSchema(id=role.id, name=role.name) for role in role_list]


@router.post('/')
async def create(
    role_data: RoleName,
    role_service: RoleService = Depends(get_role_service),
) -> RoleSchema:
    role = await role_service.create(name=role_data.name)
    return RoleSchema(id=role.id, name=role.name)


@router.put('/{role_id}')
async def update(
    role_id: UUID,
    role_data: RoleName,
    role_service: RoleService = Depends(get_role_service),
) -> RoleSchema:
    role = await role_service.update(role_id=role_id, name=role_data.name)
    return RoleSchema(id=role.id, name=role.name)


@router.delete('/{role_id}')
async def delete(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
) -> bool:
    return await role_service.delete(role_id=role_id)
