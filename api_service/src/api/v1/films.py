from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from models.film import Film
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get('/search', response_model=List[Film], summary="Поиск фильмов")
async def film_search(
    query: Optional[str] = None,
    genre_id: Optional[str] = Query(None, alias="genre"),
    sort: Optional[str] = Query(None),
    film_service: FilmService = Depends(get_film_service),
    page_size: int = Query(50, ge=1, le=100),
    page_number: int = Query(1, ge=1),
) -> List[Film]:
    films = await film_service.search_films(
        query=query, genre_id=genre_id, sort=sort, page_size=page_size, page_number=page_number
    )
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Films not found')

    return films


@router.get('/{film_id}', response_model=Film, summary="Получение полной информации о фильме")
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Film not found')
    return film
