from pathlib import Path

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Общие настройки, для всех тестов."""

    model_config = SettingsConfigDict(env_file='test.env', extra='ignore')

    POSTGRES_PASSWORD: str = Field('', alias='POSTGRES_PASSWORD')
    POSTGRES_DB: str = Field('test-auth-db', alias='POSTGRES_DB')
    POSTGRES_USER: str = Field('postgres', alias='POSTGRES_USER')
    POSTGRES_HOST: str = Field('test-auth-db', alias='POSTGRES_HOST')
    POSTGRES_PORT: int = Field(5432, alias='POSTGRES_PORT')

    REDIS_HOST: str = Field('127.0.0.1', alias='REDIS_HOST')
    REDIS_PORT: int = Field(6379, alias='REDIS_PORT')


settings = CommonSettings()
