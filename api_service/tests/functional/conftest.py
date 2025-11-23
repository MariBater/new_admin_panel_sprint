import asyncio
import pytest_asyncio


pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.cleanup",
    "tests.fixtures.helpers",
]


@pytest_asyncio.fixture(scope='session')
def event_loop(request):
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
