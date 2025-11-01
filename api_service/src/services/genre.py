from functools import lru_cache
from typing import List
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis import Redis
from services.caching import redis_cache
from models.genre import Genre
from db.elastic import get_elastic
from db.redis import get_redis


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    @redis_cache(key_prefix='genre_by_id', model=Genre, single_item=True)
    async def get_by_id(self, genre_id: str) -> Genre | None:
        return await self._get_by_id_from_elastic(genre_id=genre_id)

    @redis_cache(key_prefix='genre_list', model=Genre)
    async def get_all(self) -> List[Genre]:
        return await self._get_all_from_elastic()

    async def _get_by_id_from_elastic(self, genre_id) -> Genre | None:
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_all_from_elastic(self, page_size: int = 50) -> List[Genre]:
        try:
            body = {
                "query": {"match_all": {}},
                "size": page_size,
            }
            elastic_response = await self.elastic.search(index="genres", body=body)
            return [
                Genre(**item["_source"]) for item in elastic_response["hits"]["hits"]
            ]
        except Exception as e:

            return []


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
