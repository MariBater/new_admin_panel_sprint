import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import redis.asyncio as aioredis

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.models.entity import User
from src.core.dependencies import get_current_user, require_superuser
from src.db.postgres import get_session, Base

from src.repositories.role_repository import PgRoleRepository
from src.repositories.user_repository import PgUserRepository

from src.services.role import RoleService, get_role_service
from src.services.user import get_user_service
from src.services.auth import get_auth_service

from src.api.v1.roles import router as role_router
from src.api.v1.users import router as users_router
from src.api.v1.auth import router as auth_router

from tests.functional.settings import settings

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
