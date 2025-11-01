from http import HTTPStatus
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from services.person import PersonService, get_person_service
from schemas.film import Film
from schemas.person import PersonExtended, map_person_films

router = APIRouter()


@router.get("/search", summary='Поиск по персонам', response_model=List[PersonExtended])
async def person_search(
    query: str | None = None,
    page_number: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 50,
    person_service: PersonService = Depends(get_person_service),
) -> List[PersonExtended]:
    (persons, person_film_list) = await person_service.search_by_persons(
        query, page_number, page_size
    )

    finded_person_list = [map_person_films(p, person_film_list) for p in persons]

    return finded_person_list


@router.get(
    "/{person_id}", summary='Информация о персоне', response_model=PersonExtended
)
async def person_details(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> PersonExtended:
    (person, person_film_list) = await person_service.get_person_details(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return map_person_films(person, person_film_list)


@router.get("/{person_id}/film", summary='Фильмы по персоне', response_model=List[Film])
async def person_film(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
):
    person_film_list = await person_service.get_person_film(person_id)
    return [
        Film(uuid=uuid.UUID(film.id), title=film.title, imdb_rating=film.imdb_rating)
        for film in person_film_list
    ] or []
