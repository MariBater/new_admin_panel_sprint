from functools import lru_cache
from typing import List
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis
from repositories.genre_repository import (
    ElasticGenreRepository,
    GenreRepository,
)
from services.caching import redis_cache
from models.genre import Genre
from db.elastic import get_elastic
from db.redis import get_redis
from .cache_abc import AsyncCache
from .redis_cache import RedisCache


class GenreService:

    def __init__(self, cache: AsyncCache, genre_repository: GenreRepository, **kwargs):
        self.cache = cache
        self.genre_repository = genre_repository

    @redis_cache(key_prefix='genre_by_id', model=Genre, single_item=True)
    async def get_by_id(self, genre_id: str) -> Genre | None:
        return await self.genre_repository.get_by_id(genre_id=genre_id)

    @redis_cache(key_prefix='genre_list', model=Genre)
    async def get_all(self, page_number: int = 1, page_size: int = 50) -> List[Genre]:
        return await self.genre_repository.get_all(
            page_number=page_number, page_size=page_size
        )

    @redis_cache(key_prefix='search_genre_list', model=Genre)
    async def search(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Genre]:
        # Предполагаем, что в репозитории будет метод search
        return await self.genre_repository.search(
            query=query, page_number=page_number, page_size=page_size
        )


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    genre_repository = ElasticGenreRepository(elastic)

    return GenreService(RedisCache(redis), genre_repository)
