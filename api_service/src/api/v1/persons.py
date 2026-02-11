from http import HTTPStatus
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from core.auth_depends import RoleEnum, require_roles
from schemas.user import User
from services.person import PersonService, get_person_service
from .dependencies import PaginationParams
from schemas.film import Film
from schemas.person import PersonExtended, map_person_films
 
router = APIRouter(
    dependencies=[
        Depends(require_roles(roles=[RoleEnum.ADMIN, RoleEnum.USER, RoleEnum.PREMIUM_USER]))
    ]
)

@router.get("/search", summary='Поиск по персонам', response_model=List[PersonExtended])
async def person_search(
    query: Annotated[str | None, Query(description='Текст для поиска по имени')] = None,
    pagination: PaginationParams = Depends(),
    person_service: PersonService = Depends(get_person_service),
) -> List[PersonExtended]:
    """
    Поиск персоналий (актеры, режиссеры, сценаристы) по имени.
    Возвращает список персон с фильмами, в которых они участвовали.
    Если `query` не указан, возвращает список всех персон.
    """
    search_person_details = await person_service.search_by_persons(
        query=query,
        page_number=pagination.page_number,
        page_size=pagination.page_size,
    )

    finded_person_list = [
        map_person_films(p, search_person_details.films)
        for p in search_person_details.persons
    ]

    return finded_person_list


@router.get(
    "/{person_id}", summary='Информация о персоне', response_model=PersonExtended
)
async def person_details(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> PersonExtended:
    """
    Возвращает полную информацию о персоне (имя и фильмы с ее участием).
    """
    person_details = await person_service.get_person_details(person_id=person_id)
    if not person_details:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return map_person_films(person_details.person, person_details.films)


@router.get("/{person_id}/film", summary='Фильмы по персоне', response_model=List[Film])
async def person_film(
    person_id: str,
    person_service: PersonService = Depends(get_person_service),
) -> List[Film]:
    """
    Возвращает список фильмов, в создании которых принимала участие указанная персона.
    """
    person_film_list = await person_service.get_person_film(person_id=person_id)
    return person_film_list
