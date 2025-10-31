from typing import Optional, Type, TypeVar

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import BaseModel

from services.caching import redis_cache

Model = TypeVar("Model", bound=BaseModel)


class BaseService:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic
        self.model: Type[Model] = None
        self.index_name: str = ""

    @redis_cache(key_prefix='item_by_id', single_item=True)
    async def get_by_id(self, item_id: str) -> Optional[Model]:
        try:
            doc = await self.elastic.get(index=self.index_name, id=item_id)
            return self.model(**doc['_source'])
        except NotFoundError:
            return None
    
    @redis_cache(key_prefix='items_search')
    async def search(self, query: str, page_number: int, page_size: int) -> list[Model]:
        search_query = {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["*"],
                    "fuzziness": "AUTO"
                }
            } if query else {"match_all": {}}
        }
        response = await self.elastic.search(index=self.index_name, body=search_query)
        items = [self.model(**hit['_source']) for hit in response['hits']['hits']]
        return items