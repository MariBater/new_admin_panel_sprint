import asyncio
import json

import aiohttp
from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import pytest_asyncio
from settings import settings, indexes, ESIndexSettings


@pytest_asyncio.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=settings.es_url, verify_certs=False)
    yield client
    await client.close()


@pytest_asyncio.fixture(name='redis_client', scope='session')
async def redis_client():
    client = Redis(host=settings.redis_host, port=settings.redis_port, db=0)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def clear_cache(redis_client):
    """Очищает кеш Redis перед каждым тестом."""
    await redis_client.flushall()


@pytest_asyncio.fixture(autouse=True)
async def es_clear_data(es_client):
    """Очищает данные в индексах перед каждым тестом."""
    for index_settings in indexes:
        if await es_client.indices.exists(index=index_settings.index_name):
            await es_client.delete_by_query(index=index_settings.index_name, query={"match_all": {}})
    yield


@pytest_asyncio.fixture(name='es_write_data')
async def es_write_data(es_client):
    async def inner(data: list[dict] | ESIndexSettings):
        bulk_query = []
        if isinstance(data, ESIndexSettings):
            with open(data.data_file_path) as f:
                docs = json.load(f)
            for doc in docs:
                bulk_query.append({'_index': data.index_name, '_id': doc['id'], '_source': doc})

            # Ensure index exists before writing
            if not await es_client.indices.exists(index=data.index_name):
                with open(data.schema_file_path) as f:
                    schema = json.load(f)
                await es_client.indices.create(index=data.index_name, mappings=schema.get('mappings'), settings=schema.get('settings'))

        else:
            bulk_query = data

        updated, errors = await async_bulk(client=es_client, actions=bulk_query)
        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')
        await es_client.indices.refresh(index='_all')
    return inner


@pytest_asyncio.fixture(name='make_get_request')
async def make_get_request():

    async with aiohttp.ClientSession() as session:
        async def inner(path: str, data: dict = None):
            url = settings.api_base_url + path
            async with session.get(url, params=data) as response:
                try:
                    body = await response.json()
                except aiohttp.client_exceptions.ContentTypeError:
                    body = await response.text()
                headers = response.headers
                status = response.status
            return body, headers, status
        yield inner