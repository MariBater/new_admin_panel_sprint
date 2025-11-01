from http import HTTPStatus
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from schemas.person import Person
from schemas.genre import Genre
from schemas.film import Film, FilmExtended
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get(
    '/',
    summary='Популярные фильмы с возможностью фильтарции по жанрам',
    response_model=List[Film],
)
async def films(
    genre: Optional[str] = None,
    sort: Optional[str] = None,
    page_number: int = 1,
    page_size: int = 50,
    film_service: FilmService = Depends(get_film_service),
) -> List[Film]:

    film_list = await film_service.get_all(
        genre=genre, sort=sort, page_number=page_number, page_size=page_size
    )

    return [
        Film(uuid=uuid.UUID(film.id), title=film.title, imdb_rating=film.imdb_rating)
        for film in film_list
    ]


@router.get(
    '/search',
    summary='Поиск по фильмам',
    response_model=List[Film],
)
async def films_search(
    query: str,
    page_number: int = 1,
    page_size: int = 50,
    film_service: FilmService = Depends(get_film_service),
) -> List[Film]:
    film_list = await film_service.search(
        query=query, page_number=page_number, page_size=page_size
    )

    return [
        Film(uuid=uuid.UUID(film.id), title=film.title, imdb_rating=film.imdb_rating)
        for film in film_list
    ]


@router.get(
    '/{film_id}', summary='Полная информация по фильму', response_model=FilmExtended
)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id=film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return FilmExtended(
        uuid=uuid.UUID(film.id),
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genre=[Genre(uuid=uuid.UUID(item.id), name=item.name) for item in film.genres],
        actors=[
            Person(uuid=uuid.UUID(item.id), full_name=item.full_name)
            for item in film.actors
        ],
        writers=[
            Person(uuid=uuid.UUID(item.id), full_name=item.full_name)
            for item in film.writers
        ],
        directors=[
            Person(uuid=uuid.UUID(item.id), full_name=item.full_name)
            for item in film.directors
        ],
    )
