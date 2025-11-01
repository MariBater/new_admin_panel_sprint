from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.genre import Genre
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get("/{genre_id}", summary='Информация по жанру', response_model=Genre)
async def genre_details(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    return Genre(uuid=genre.id, name=genre.name)


@router.get("/", summary='Список жанров', response_model=List[Genre])
async def genres(
    genre_service: GenreService = Depends(get_genre_service),
) -> List[Genre]:
    genre_list = await genre_service.get_all()
    return [Genre(uuid=g.id, name=g.name) for g in genre_list]
