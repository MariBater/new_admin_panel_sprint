import logging
from logging import config as logging_config
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from api.v1 import films, genres, persons
from core.config import settings
from core.logger import LOGGING
from db import elastic as elastic_db
from db import redis as redis_db

logging_config.dictConfig(LOGGING)
app_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        app_logger.info("Attempting to connect to Redis...")
        redis_db.redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        await redis_db.redis.ping()
        app_logger.info("Successfully connected to Redis.")
    except Exception as e:
        app_logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
        # Optionally re-raise to prevent startup if Redis is critical
        # raise
    try:
        app_logger.info("Attempting to connect to Elasticsearch...")
        elastic_db.es = AsyncElasticsearch(
            hosts=[settings.ELASTIC_HOST],
        )
        await elastic_db.es.info()
        app_logger.info("Successfully connected to Elasticsearch.")
    except Exception as e:
        app_logger.error(f"Failed to connect to Elasticsearch: {e}", exc_info=True)
        # raise
    yield
    # Shutdown
    if redis_db.redis:
        await redis_db.redis.close()
        app_logger.info("Redis connection closed.")
    if elastic_db.es:
        await elastic_db.es.close()
        app_logger.info("Elasticsearch connection closed.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
# Подключение роутеров к приложению.
# Теги используются для группировки эндпоинтов в документации.
app.include_router(films.router, prefix='/api/v1/films', tags=['Фильмы'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['Жанры'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['Персоналии'])
