from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from models.film import Film
from models.person import Person
from services.person import PersonService, get_person_service
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get('/search', response_model=List[Person], summary="Поиск персоналий")
async def person_search(
    query: str,
    person_service: PersonService = Depends(get_person_service),
    page_size: int = Query(50, ge=1, le=100),
    page_number: int = Query(1, ge=1),
) -> List[Person]:
    persons = await person_service.search_persons(query=query, page_size=page_size, page_number=page_number)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Persons not found')
    return persons


@router.get('/{person_id}', response_model=Person, summary="Получение информации о персоналии")
async def person_details(
    person_id: str, person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Person not found')
    return person


@router.get('/{person_id}/films', response_model=List[Film], summary="Получение фильмов с участием персоналии")
async def person_films(
    person_id: str,
    film_service: FilmService = Depends(get_film_service),
    page_size: int = Query(50, ge=1, le=100),
    page_number: int = Query(1, ge=1),
) -> List[Film]:
    films = await film_service.get_films_by_person(
        person_id=person_id, page_size=page_size, page_number=page_number
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Films not found for this person')
    return films