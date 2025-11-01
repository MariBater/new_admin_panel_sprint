import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=f'.env', env_file_encoding='utf-8')

    # Название проекта. Используется в Swagger-документации
    PROJECT_NAME: str = Field('movies', alias='PROJECT_NAME')

    # Redis
    REDIS_HOST: str = Field('127.0.0.1', alias='REDIS_HOST')
    REDIS_PORT: int = Field(6379, alias='REDIS_PORT')

    # Elasticsearch
    ELASTIC_SCHEMA: str = Field('http://', alias='ELASTIC_SCHEMA')
    ELASTIC_HOST: str = Field('127.0.0.1', alias='ELASTIC_HOST')
    ELASTIC_PORT: int = Field(9200, alias='ELASTIC_PORT')

    # Время жизни кеша
    CACHE_EXPIRE_IN_SECONDS: int = 300


settings = Settings()
