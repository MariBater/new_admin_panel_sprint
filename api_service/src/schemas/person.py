from collections import defaultdict
from typing import List
import uuid
from pydantic import UUID4, BaseModel


class Person(BaseModel):
    uuid: UUID4
    full_name: str


class FilmPerson(BaseModel):
    id: str
    roles: List[str]


class PersonExtended(Person):
    films: List[FilmPerson]


def map_person_films(person, person_film_list) -> PersonExtended:

    film_roles = defaultdict(list)

    for film in person_film_list:
        if person.full_name in film.actors_names:
            film_roles[film.id].append("actors")
        if person.full_name in film.writers_names:
            film_roles[film.id].append("writers")
        if person.full_name in film.directors_names:
            film_roles[film.id].append("directors")

    films = [
        FilmPerson(id=film_id, roles=roles) for film_id, roles in film_roles.items()
    ]

    return PersonExtended(
        uuid=uuid.UUID(person.id),
        full_name=person.full_name,
        films=films,
    )
