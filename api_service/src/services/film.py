from functools import lru_cache
from typing import List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from services.caching import redis_cache
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film, FilmExtended


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    @redis_cache(key_prefix='film_by_id', model=FilmExtended, single_item=True)
    async def get_by_id(self, film_id: str) -> Optional[FilmExtended]:
        return await self._get_film_from_elastic(film_id)

    @redis_cache(key_prefix='genre_list', model=Film)
    async def get_all(
        self,
        genre: Optional[str] = None,
        sort: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:
        return await self._get_films_from_elastic(
            genre=genre, sort=sort, page_number=page_number, page_size=page_size
        )

    @redis_cache(key_prefix='search_genre_list', model=Film)
    async def search(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:

        return await self._searh_films_from_elastic(
            query=query, page_number=page_number, page_size=page_size
        )

    async def _searh_films_from_elastic(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:
        try:
            query_body = {"match_all": {}}
            if query:
                query_body = {
                    "multi_match": {"query": query, 'fields': ["title", "description"]}
                }

            body = {
                "query": query_body,
                "from": (page_number - 1) * page_size,
                "size": page_size,
            }

            elastic_response = await self.elastic.search(index='movies', body=body)
            return [
                FilmExtended(**item["_source"])
                for item in elastic_response["hits"]["hits"]
            ]
        except NotFoundError:
            return []

    async def _get_films_from_elastic(
        self,
        genre: Optional[str] = None,
        sort: Optional[str] = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]:
        try:
            query_sort = []
            if sort:
                sort_order = 'asc'
                if '-' in sort:
                    sort_order = 'desc'
                    sort = sort[1:]
                query_sort = [{sort: {"order": sort_order}}]

            query = {"match_all": {}}
            if genre:
                query = {
                    "bool": {
                        "filter": [
                            {
                                "nested": {
                                    "path": "genres",
                                    "query": {"term": {"genres.id": genre}},
                                }
                            }
                        ],
                    },
                }

            body = {
                "query": query,
                "sort": query_sort,
                "from": (page_number - 1) * page_size,
                "size": page_size,
            }

            elastic_response = await self.elastic.search(index='movies', body=body)
            return [
                FilmExtended(**item["_source"])
                for item in elastic_response["hits"]["hits"]
            ]
        except NotFoundError:
            return []

    async def _get_film_from_elastic(self, film_id: str) -> Optional[FilmExtended]:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        return FilmExtended(**doc['_source'])


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
