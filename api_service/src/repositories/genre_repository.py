from typing import List, Protocol

from elasticsearch import AsyncElasticsearch, NotFoundError

from models.genre import Genre


class GenreRepository(Protocol):
    async def get_by_id(self, genre_id) -> Genre | None: ...
    async def get_all(
        self, page_number: int = 1, page_size: int = 50
    ) -> List[Genre]: ...
    async def search(
        self, query: str, page_number: int = 1, page_size: int = 50
    ) -> List[Genre]: ...
    async def search(
        self, query: str, page_number: int = 1, page_size: int = 50
    ) -> List[Genre]: ...


class ElasticGenreRepository:

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_by_id(self, genre_id) -> Genre | None:
        try:
            doc = await self.elastic.get(index='genres', id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def get_all(
        self, page_number: int = 1, page_size: int = 50
    ) -> List[Genre]:
        try:
            from_ = (page_number - 1) * page_size
            body = {
                "query": {"match_all": {}},
                "from": from_,
                "size": page_size,
            }
            elastic_response = await self.elastic.search(index="genres", body=body)
            return [
                Genre(**item["_source"]) for item in elastic_response["hits"]["hits"]
            ]
        except Exception:  # Ловим любую ошибку от Elasticsearch (включая выход за пределы окна)
            return []

    async def search(
        self, query: str, page_number: int = 1, page_size: int = 50
    ) -> List[Genre]:
        try:
            from_ = (page_number - 1) * page_size
            body = {
                "query": {
                    "query_string": {
                        "query": f"*{query}*", "fields": ["name", "description"]
                    }
                },
                "from": from_,
                "size": page_size,
            }
            elastic_response = await self.elastic.search(index="genres", body=body)
            return [
                Genre(**item["_source"]) for item in elastic_response["hits"]["hits"]
            ]
        except Exception:
            return []
