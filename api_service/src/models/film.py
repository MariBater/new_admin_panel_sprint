from typing import List, Optional
from pydantic import BaseModel


class PersonInFilm(BaseModel):
    id: str
    name: str


class GenreInFilm(BaseModel):
    id: str
    name: str


class Film(BaseModel):
    id: str
    title: str
    description: Optional[str]
    imdb_rating: Optional[float]
    genres: List[GenreInFilm] = []
    actors: List[PersonInFilm] = []
    writers: List[PersonInFilm] = []
