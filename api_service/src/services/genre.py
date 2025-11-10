from functools import lru_cache
from typing import List
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis import Redis
from repositories.genre_repository import (
    ElasticGenreRepository,
    GenreRepository,
)
from services.caching import redis_cache
from models.genre import Genre
from db.elastic import get_elastic
from db.redis import get_redis


class GenreService:

    def __init__(self, redis: Redis, genre_repository: GenreRepository):
        self.redis = redis
        self.genre_repository = genre_repository

    @redis_cache(key_prefix='genre_by_id', model=Genre, single_item=True)
    async def get_by_id(self, genre_id: str) -> Genre | None:
        return await self.genre_repository.get_by_id(genre_id=genre_id)

    @redis_cache(key_prefix='genre_list', model=Genre)
    async def get_all(self) -> List[Genre]:
        return await self.genre_repository.get_all()


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    genre_repository = ElasticGenreRepository(elastic)
    return GenreService(redis, genre_repository)
