from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre
from services.base import BaseService


class GenreService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.redis = redis
        self.index_name = 'genres'
        self.model = Genre

@lru_cache()
def get_genre_service(redis: Redis = Depends(get_redis), elastic: AsyncElasticsearch = Depends(get_elastic)) -> GenreService:
    return GenreService(redis, elastic)