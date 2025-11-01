from functools import lru_cache
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis import Redis
from services.caching import redis_cache
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import FilmExtended
from models.person import Person


class PersonService:

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_person_details(
        self, person_id: str
    ) -> tuple[Person | None, list[FilmExtended]]:
        person = await self._get_person_from_elastic(person_id=person_id)
        person_films_list = await self._get_film_by_person_ids(person_ids=[person_id])

        if not person:
            return None, []

        return person, person_films_list

    async def get_person_film(self, person_id: str) -> list[FilmExtended]:
        return await self._get_film_by_person_ids(person_ids=[person_id])

    async def search_by_persons(
        self, query: str | None, page_number: int = 1, page_size: int = 50
    ) -> tuple[list[Person], list[FilmExtended]]:
        persons_list = await self._search_persons_from_elastic(
            query=query, page_number=page_number, page_size=page_size
        )

        person_ids = [p.id for p in persons_list]
        films_list = await self._get_film_by_person_ids(person_ids=person_ids)

        return persons_list, films_list

    @redis_cache(key_prefix="person", model=Person, single_item=True)
    async def _get_person_from_elastic(self, person_id: str) -> Person | None:
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
            return Person(**doc["_source"])
        except NotFoundError:
            return None

    @redis_cache(key_prefix="films_by_persons", model=FilmExtended)
    async def _get_film_by_person_ids(
        self, person_ids: list[str]
    ) -> list[FilmExtended]:

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

    @redis_cache(key_prefix="search_persons_films", model=Person)
    async def _search_persons_from_elastic(
        self, query: str | None, page_number: int = 1, page_size: int = 50
    ) -> list[Person]:
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


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
