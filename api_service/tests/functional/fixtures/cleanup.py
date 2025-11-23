import pytest_asyncio
from settings import indexes


@pytest_asyncio.fixture(autouse=True)
async def clear_cache(redis_client):
    """Очищает кеш Redis перед каждым тестом."""
    await redis_client.flushall()


@pytest_asyncio.fixture(autouse=True)
async def es_clear_data(es_client):
    """Очищает данные в индексах перед каждым тестом."""
    for index_settings in indexes:
        if await es_client.indices.exists(index=index_settings.index_name):
            await es_client.delete_by_query(
                index=index_settings.index_name, query={"match_all": {}}
            )
    yield
