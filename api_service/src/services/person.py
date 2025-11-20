from functools import lru_cache
from typing import List
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis
from models.person_details import PersonDetails, SearchPersonsDetails
from services.cache_abc import AsyncCache
from services.caching import redis_cache
from repositories.person_repository import ElasticPersonRepository
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import FilmExtended
from .redis_cache import RedisCache


class PersonService:

    def __init__(
        self, cache: AsyncCache, person_repository: ElasticPersonRepository, **kwargs
    ):
        self.cache = cache
        self.person_repository = person_repository

    @redis_cache(key_prefix="person_details", model=PersonDetails, single_item=True)
    async def get_person_details(self, person_id: str) -> PersonDetails | None:
        person = await self.person_repository.get_by_id(person_id=person_id)
        person_films_List = await self.person_repository.get_film_by_person_ids(
            person_ids=[person_id]
        )

        if not person:
            return None

        return PersonDetails(person=person, films=person_films_List)

    @redis_cache(key_prefix="films_by_persons", model=FilmExtended)
    async def get_person_film(self, person_id: str) -> List[FilmExtended]:
        return await self.person_repository.get_film_by_person_ids(
            person_ids=[person_id]
        )

    @redis_cache(
        key_prefix="search_persons", model=SearchPersonsDetails, single_item=True
    )
    async def search_by_persons(
        self, query: str | None, page_number: int = 1, page_size: int = 50
    ) -> SearchPersonsDetails:
        persons_List = await self.person_repository.search_persons(
            query=query, page_number=page_number, page_size=page_size
        )

        person_ids = [p.id for p in persons_List]
        films_List = await self.person_repository.get_film_by_person_ids(
            person_ids=person_ids
        )

        return SearchPersonsDetails(persons=persons_List, films=films_List)


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    person_repository = ElasticPersonRepository(elastic)
    return PersonService(RedisCache(redis), person_repository)
