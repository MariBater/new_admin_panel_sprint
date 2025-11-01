from pydantic import BaseModel, Field


class Person(BaseModel):
    id: str
    full_name: str = Field(alias='name')

    class Config:

        populate_by_name = True
        extra = 'ignore'
