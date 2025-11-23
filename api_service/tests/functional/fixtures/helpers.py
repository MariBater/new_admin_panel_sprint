import json

import aiohttp
from elasticsearch.helpers import async_bulk
import pytest_asyncio
from settings import settings, ESIndexSettings


@pytest_asyncio.fixture(name='es_write_data')
async def es_write_data(es_client):
    async def inner(data: list[dict] | ESIndexSettings):
        bulk_query = []
        if isinstance(data, ESIndexSettings):
            with open(data.data_file_path) as f:
                docs = json.load(f)
            for doc in docs:
                bulk_query.append(
                    {'_index': data.index_name, '_id': doc['id'], '_source': doc}
                )

            # Ensure index exists before writing
            if not await es_client.indices.exists(index=data.index_name):
                with open(data.schema_file_path) as f:
                    schema = json.load(f)
                await es_client.indices.create(
                    index=data.index_name,
                    mappings=schema.get('mappings'),
                    settings=schema.get('settings'),
                )

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
