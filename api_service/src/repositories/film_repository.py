from typing import List, Protocol

from elasticsearch import AsyncElasticsearch, NotFoundError

from models.film import Film, FilmExtended


class FilmRepository(Protocol):
    async def get_film_by_id(self, film_id: str) -> FilmExtended | None: ...

    async def get_films_by_genre(
        self,
        genre: str | None = None,
        sort: str | None = None,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]: ...

    async def searh_films(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 50,
    ) -> List[Film]: ...


class ElasticFilmRepository:

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    async def get_film_by_id(self, film_id: str) -> FilmExtended | None:
        try:
            doc = await self.elastic.get(index='movies', id=film_id)
        except NotFoundError:
            return None
        return FilmExtended(**doc['_source'])

    async def get_films_by_genre(
        self,
        genre: str | None = None,
        sort: str | None = None,
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

    async def searh_films(
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
