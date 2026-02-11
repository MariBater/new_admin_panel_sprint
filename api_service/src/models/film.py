from typing import List
from pydantic import BaseModel
from .genre import Genre
from .person import Person


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float


class FilmExtended(Film):
    description: str
    directors_names: List[str]
    actors_names: List[str]
    writers_names: List[str]
    actors: List[Person]
    writers: List[Person]
    directors: List[Person]
    genres: List[Genre]
