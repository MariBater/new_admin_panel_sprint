from typing import List, Protocol

import backoff
from elastic_transport import ConnectionError
from elasticsearch import AsyncElasticsearch, NotFoundError

from models.genre import Genre


class GenreRepository(Protocol):
    async def get_by_id(self, genre_id) -> Genre | None: ...
    async def get_all(self, page_size: int = 50) -> List[Genre]: ...


class ElasticGenreRepository:

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    @backoff.on_exception(backoff.expo, (ConnectionError), max_time=30)
    async def get_by_id(self, genre_id) -> Genre | None:
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    @backoff.on_exception(backoff.expo, (ConnectionError), max_time=30)
    async def get_all(self, page_size: int = 50) -> List[Genre]:
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
