from functools import lru_cache
from typing import List

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from repositories.film_repository import ElasticFilmRepository
from services.cache_abc import AsyncCache
from services.caching import redis_cache
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film, FilmExtended
from .redis_cache import RedisCache


class FilmService:

    def __init__(
        self, cache: AsyncCache, film_repository: ElasticFilmRepository, **kwargs
    ):
        self.cache = cache
        self.film_repository = film_repository

    @redis_cache(key_prefix='film_by_id', model=FilmExtended, single_item=True)
    async def get_by_id(self, film_id: str) -> FilmExtended | None:
        return await self.film_repository.get_film_by_id(film_id)

    @redis_cache(key_prefix='genre_list', model=Film)
    async def get_all(
        self,
        genre: str | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:
        return await self.film_repository.get_films_by_genre(
            genre=genre, sort=sort, page_number=page_number, page_size=page_size
        )

    @redis_cache(key_prefix='search_genre_list', model=Film)
    async def search(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:

        return await self.film_repository.searh_films(
            query=query, page_number=page_number, page_size=page_size
        )


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    film_repository = ElasticFilmRepository(elastic)

    return FilmService(RedisCache(redis), film_repository)
