import asyncio
import json
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# Добавляем корневую директорию проекта в sys.path
# Это позволяет использовать абсолютные импорты от корня проекта (например, `from src...`)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
src_path = project_root / "api_service" / "src"
sys.path.insert(0, str(src_path))

# Импортируем основное приложение api_service
from api_service.src.main import app as api_app


# Абсолютные импорты для устранения неоднозначности
from auth_service.src.models.entity import User
from auth_service.src.core.dependencies import get_current_user, require_superuser
from auth_service.src.db.postgres import get_session
from auth_service.src.api.v1.roles import router as role_router
from auth_service.src.api.v1.users import router as users_router
from auth_service.src.api.v1.auth import router as auth_router

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для создания HTTP клиента для тестового приложения."""
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as _client:
        yield _client


@pytest_asyncio.fixture(name='make_get_request')
async def make_get_request(client: AsyncClient):
    """Новая фикстура для выполнения GET запросов через тестовый клиент."""
    async def inner(path: str, data: dict = None):
        response = await client.get(f"/api/v1{path}", params=data)
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = response.text
        headers = response.headers
        status = response.status_code
        return body, headers, status
    return inner
