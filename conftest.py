# This file is required for pytest to discover and apply plugins correctly.
import asyncio

import pytest


pytest_plugins = [
    "api_service.tests.functional.fixtures.database",
    "api_service.tests.functional.fixtures.cleanup",
    "api_service.tests.functional.fixtures.helpers",
]

@pytest.fixture(scope="session")
def event_loop():
    """Create a single, session-wide event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()