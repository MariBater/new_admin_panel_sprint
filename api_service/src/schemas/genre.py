from pydantic import UUID4, BaseModel


class Genre(BaseModel):
    uuid: UUID4
    name: str
