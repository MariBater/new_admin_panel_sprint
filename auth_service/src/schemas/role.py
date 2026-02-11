from uuid import UUID
from pydantic import BaseModel


class RoleName(BaseModel):
    name: str


class RoleSchema(BaseModel):
    id: UUID
    name: str


class RoleUserSchema(BaseModel):
    user_id: UUID
    role_name: str
