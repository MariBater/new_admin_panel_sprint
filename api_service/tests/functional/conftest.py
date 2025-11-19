import asyncio
import json
from pathlib import Path
import aiohttp
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
import pytest_asyncio
from functional.settings import test_settings


@pytest_asyncio.fixture(scope='session')
async def aiohttp_session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest_asyncio.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name='es_client', scope='session')
async def es_client():
    es_client = AsyncElasticsearch(hosts=test_settings.es_host, verify_certs=False)
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name='es_write_data')
async def es_write_data(es_client):
    async def inner(data: list[dict]):
        schema_path = Path(__file__).parent / "elastic_schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            es_schema = json.load(f)

            for index_name, schema in es_schema.items():
                if await es_client.indices.exists(index=index_name):
                    await es_client.indices.delete(index=index_name)

                await es_client.indices.create(index=index_name, **schema)

            updated, errors = await async_bulk(client=es_client, actions=data)

            for index_name, schema in es_schema.items():
                await es_client.indices.refresh(index=index_name)
            await es_client.close()

        if errors:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner


@pytest_asyncio.fixture(name='make_get_request')
def make_get_request(aiohttp_session):

    async def inner(path: str, data: dict):
        url = test_settings.service_url + path
        async with aiohttp_session.get(url, params=data) as response:
            body = await response.json()
            headers = response.headers
            status = response.status
        return body, headers, status

    return inner
