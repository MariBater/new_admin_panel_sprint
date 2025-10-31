from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from services.caching import redis_cache
from models.film import Film
from services.base import BaseService


class FilmService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        super().__init__(elastic)
        self.redis = redis
        self.index_name = 'movies'
        self.model = Film

    @redis_cache(key_prefix='films_search')
    async def search_films(
        self,
        query: Optional[str],
        genre_id: Optional[str],
        sort: Optional[str],
        page_number: int,
        page_size: int,
    ) -> list[Film]:
        search_query = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": {"bool": {"must": []}},
        }

        if query:
            search_query["query"]["bool"]["must"].append(
                {"multi_match": {"query": query, "fields": ["title", "description"]}}
            )

        if genre_id:
            search_query["query"]["bool"]["must"].append(
                {"nested": {"path": "genres", "query": {"term": {"genres.id": genre_id}}}}
            )

        if not search_query["query"]["bool"]["must"]:
            search_query["query"] = {"match_all": {}}

        if sort:
            field = sort.lstrip('-')
            order = "desc" if sort.startswith('-') else "asc"
            search_query["sort"] = [{field: {"order": order}}]

        response = await self.elastic.search(index=self.index_name, body=search_query)
        return [self.model(**hit['_source']) for hit in response['hits']['hits']]

    @redis_cache(key_prefix='films_by_person')
    async def get_films_by_person(self, person_id: str, page_number: int, page_size: int) -> list[Film]:
        search_query = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": {
                "bool": {
                    "should": [
                        {"nested": {"path": "actors", "query": {"term": {"actors.id": person_id}}}},
                        {"nested": {"path": "writers", "query": {"term": {"writers.id": person_id}}}},
                    ],
                    "minimum_should_match": 1
                }
            }
        }
        response = await self.elastic.search(index=self.index_name, body=search_query)
        return [self.model(**hit['_source']) for hit in response['hits']['hits']]


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
