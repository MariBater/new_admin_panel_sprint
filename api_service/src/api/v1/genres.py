from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from models.genre import Genre
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get('/', response_model=List[Genre], summary="Получение списка жанров")
async def genre_list(
    genre_service: GenreService = Depends(get_genre_service),
    page_size: int = Query(50, ge=1, le=100),
    page_number: int = Query(1, ge=1),
) -> List[Genre]:
    genres = await genre_service.search(query=None, page_size=page_size, page_number=page_number)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Genres not found')
    return genres


@router.get('/{genre_id}', response_model=Genre, summary="Получение информации о жанре по ID")
async def genre_details(
    genre_id: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Genre not found')
    return genre