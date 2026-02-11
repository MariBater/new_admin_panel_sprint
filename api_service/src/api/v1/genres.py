from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.user import User
from core.auth_depends import RoleEnum, require_roles
from schemas.genre import Genre
from .dependencies import PaginationParams
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get('/{genre_id}', response_model=Genre, summary="Информация по жанру")
async def genre_details(
    genre_id: str,
    genre_service: GenreService = Depends(get_genre_service),
    current_user: User = Depends(
        require_roles(roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER])
    ),
) -> Genre:
    """Получение жанра по его id"""
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    return Genre(uuid=genre.id, name=genre.name)


@router.get("/", summary='Список жанров', response_model=List[Genre])
async def genres(
    pagination: PaginationParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
    current_user: User = Depends(
        require_roles(roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER])
    ),
) -> List[Genre]:
    """Получение списка жанров с пагинацией."""
    genre_list = await genre_service.get_all(
        page_number=pagination.page_number, page_size=pagination.page_size
    )

    return [Genre(uuid=g.id, name=g.name) for g in genre_list]


@router.get("/search/", summary='Поиск по жанрам', response_model=List[Genre])
async def genre_search(
    query: Annotated[str, Query(min_length=1, description='Текст для поиска')],
    pagination: PaginationParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
    current_user: User = Depends(
        require_roles(roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER])
    ),
) -> List[Genre]:
    """Поиск жанров по названию."""

    genre_list = await genre_service.search(
        query=query, page_number=pagination.page_number, page_size=pagination.page_size
    )

    return [Genre(uuid=g.id, name=g.name) for g in genre_list]
