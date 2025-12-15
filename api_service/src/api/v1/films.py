from http import HTTPStatus
from typing import Annotated, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.user import User
from core.auth_depends import RoleEnum, require_roles
from schemas.person import Person
from schemas.genre import Genre
from schemas.film import Film, FilmExtended
from .dependencies import PaginationParams
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get(
    '/',
    summary='Популярные фильмы с возможностью фильтарции по жанрам',
    response_model=List[Film],
)
async def films(
    genre: Annotated[str | None, Query(description='Фильтр по ID жанра')] = None,
    sort: Annotated[
        str | None,
        Query(description='Сортировка по рейтингу (imdb_rating или -imdb_rating)'),
    ] = None,
    pagination: PaginationParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
    current_user: User = Depends(
        require_roles(
            roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER],
            use_auth_service=True,
        )
    ),
) -> List[Film]:
    """
    Возвращает список фильмов.

    - **Сортировка**: по полю `imdb_rating`. Для сортировки по убыванию используйте `-imdb_rating`.
    - **Фильтрация**: по жанру (`genre`).
    - **Пагинация**: параметры `page_number` и `page_size`.
    """

    film_list = await film_service.get_all(
        genre=genre,
        sort=sort,
        page_number=pagination.page_number,
        page_size=pagination.page_size,
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
    query: Annotated[str, Query(description='Текст для поиска', min_length=3)],
    pagination: PaginationParams = Depends(),
    film_service: FilmService = Depends(get_film_service),
    current_user: User = Depends(
        require_roles(roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER])
    ),
) -> List[Film]:
    """
    Полнотекстовый поиск по фильмам.
    Поиск осуществляется по названию и описанию фильма.
    """
    film_list = await film_service.search(
        query=query,
        page_number=pagination.page_number,
        page_size=pagination.page_size,
    )

    return [
        Film(uuid=uuid.UUID(film.id), title=film.title, imdb_rating=film.imdb_rating)
        for film in film_list
    ]


@router.get(
    '/{film_id}', summary='Полная информация по фильму', response_model=FilmExtended
)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service),
    current_user: User = Depends(
        require_roles(roles=[RoleEnum.ADMIN, RoleEnum.PREMIUM_USER])
    ),
) -> Film:
    """
    Возвращает полную информацию о фильме по его ID.
    """
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
