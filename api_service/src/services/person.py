from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person
from services.caching import redis_cache
from services.base import BaseService


class PersonService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.redis = redis
        self.index_name = 'persons'
        self.model = Person

    @redis_cache(key_prefix='persons_search')
    async def search_persons(self, query: str, page_number: int, page_size: int) -> list[Person]:
        search_query = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": {
                "match": {
                    "full_name": {"query": query, "fuzziness": "AUTO"}
                }
            } if query else {"match_all": {}}
        }
        response = await self.elastic.search(index=self.index_name, body=search_query)
        return [self.model(**hit['_source']) for hit in response['hits']['hits']]


@lru_cache()
def get_person_service(redis: Redis = Depends(get_redis), elastic: AsyncElasticsearch = Depends(get_elastic)) -> PersonService:
    return PersonService(redis, elastic)