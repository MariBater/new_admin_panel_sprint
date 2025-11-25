from contextlib import asynccontextmanager
from logging import config as logging_config
import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis import Redis
from sqlalchemy import text


from api.v1 import auth, roles
from core.logger import LOGGING
from core.config import settings
from db import redis as redis_db
from db import postgres as posrgres_db


logging_config.dictConfig(LOGGING)
app_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        app_logger.info("Attempting to connect to Redis...")
        redis_db.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        redis_db.redis.ping()
        app_logger.info("Successfully connected to Redis.")
    except Exception as e:
        app_logger.error(f"Failed to connect to Redis: {e}", exc_info=True)

    try:
        app_logger.info("Attempting to connect to Postgres...")
        async with posrgres_db.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        app_logger.info("Database connection successful")
    except Exception as e:
        app_logger.error(f"Database connection failed: {e}")

    try:
        app_logger.info("Create table")
        await posrgres_db.create_database()
    except Exception as e:
        app_logger.error(f"Create table failed: {e}")

    yield
    # Shutdown
    if redis_db.redis:
        await redis_db.redis.close()
        app_logger.info("Redis connection closed.")

    await posrgres_db.engine.dispose()
    app_logger.info("Postgres connection closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Сервис авторизации",
    version="1.0.0",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# Подключение роутеров к приложению.
# Теги используются для группировки эндпоинтов в документации.
app.include_router(auth.router, prefix='/api/v1/auth', tags=['Авторизация'])
app.include_router(roles.router, prefix='/api/v1/roles', tags=['Управление ролями'])
