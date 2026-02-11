from typing import List
from pydantic import BaseModel, UUID4
from schemas.genre import Genre
from schemas.person import Person


class Film(BaseModel):
    uuid: UUID4
    title: str
    imdb_rating: float


class FilmExtended(Film):
    description: str
    genre: List[Genre]
    actors: List[Person]
    writers: List[Person]
    directors: List[Person]
