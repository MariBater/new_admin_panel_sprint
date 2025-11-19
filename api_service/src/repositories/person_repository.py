from typing import List, Protocol

from elasticsearch import AsyncElasticsearch, NotFoundError

from models.film import FilmExtended
from models.person import Person


class PersonRepository(Protocol):
    async def get_by_id(self, person_id: str) -> Person | None: ...
    async def get_film_by_person_ids(
        self, person_ids: List[str]
    ) -> List[FilmExtended]: ...
    async def search_persons(
        self, query: str | None, page_number: int = 1, page_size: int = 50
    ) -> List[Person]: ...


class ElasticPersonRepository:

    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic

    # @redis_cache(key_prefix="person", model=Person, single_item=True)
    async def get_by_id(self, person_id: str) -> Person | None:
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
            return Person(**doc["_source"])
        except NotFoundError:
            return None

    async def get_film_by_person_ids(self, person_ids: List[str]) -> List[FilmExtended]:

        if not person_ids:
            return []

        query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "directors",
                                "query": {"terms": {"directors.id": person_ids}},
                            }
                        },
                        {
                            "nested": {
                                "path": "actors",
                                "query": {"terms": {"actors.id": person_ids}},
                            }
                        },
                        {
                            "nested": {
                                "path": "writers",
                                "query": {"terms": {"writers.id": person_ids}},
                            }
                        },
                    ]
                }
            }
        }

        try:
            response = await self.elastic.search(index="movies", body=query)
            return [
                FilmExtended(**item["_source"]) for item in response["hits"]["hits"]
            ]
        except NotFoundError:
            return []

    #  @redis_cache(key_prefix="search_persons_films", model=Person)
    async def search_persons(
        self, query: str | None, page_number: int = 1, page_size: int = 50
    ) -> List[Person]:
        query_body = (
            {"match_all": {}}
            if not query
            else {"multi_match": {"query": query, "fields": ["full_name"]}}
        )
        body = {
            "query": query_body,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }

        try:
            response = await self.elastic.search(index="persons", body=body)
            return [Person(**item["_source"]) for item in response["hits"]["hits"]]
        except NotFoundError:
            return []
