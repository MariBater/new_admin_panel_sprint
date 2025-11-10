from typing import List

from pydantic import BaseModel
from .film import FilmExtended
from .person import Person


class PersonDetails(BaseModel):
    person: Person | None
    films: List[FilmExtended]


class SearchPersonsDetails(BaseModel):
    persons: List[Person]
    films: List[FilmExtended]
