from uuid import UUID
from pydantic import BaseModel


class RoleName(BaseModel):
    name: str


class RoleSchema(BaseModel):
    id: UUID
    name: str


class RoleUserSchema(BaseModel):
    role_id: UUID
    user_id: UUID
