from uuid import UUID
from pydantic import BaseModel


class User(BaseModel):
    id: str
    login: str
    roles: str
