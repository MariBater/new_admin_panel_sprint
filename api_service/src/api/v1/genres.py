from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.genre import Genre
from .dependencies import PaginationParams
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get('/{genre_id}', response_model=Genre, summary="Информация по жанру")
async def genre_details(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    """Получение жанра по его id"""
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    return Genre(uuid=genre.id, name=genre.name)


@router.get("/", summary='Список жанров', response_model=List[Genre])
async def genres(
    # Убираем все сложные зависимости и принимаем параметры напрямую, как в films.py
    pagination: PaginationParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
) -> List[Genre]:
    """Получение списка жанров с пагинацией."""
    
    # Вызываем метод get_all, который точно существует в вашем сервисе
    genre_list = await genre_service.get_all(
        page_number=pagination.page_number, page_size=pagination.page_size
    )
    
    return [Genre(uuid=g.id, name=g.name) for g in genre_list]


@router.get("/search/", summary='Поиск по жанрам', response_model=List[Genre])
async def genre_search(
    query: Annotated[str, Query(min_length=1, description='Текст для поиска')],
    pagination: PaginationParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
) -> List[Genre]:
    """Поиск жанров по названию."""
    
    # Предполагаем, что в GenreService есть или будет метод search
    genre_list = await genre_service.search(
        query=query, page_number=pagination.page_number, page_size=pagination.page_size
    )
    
    return [Genre(uuid=g.id, name=g.name) for g in genre_list]
