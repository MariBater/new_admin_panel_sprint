from redis.asyncio import Redis
from elasticsearch import AsyncElasticsearch
import pytest_asyncio
from settings import settings


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
