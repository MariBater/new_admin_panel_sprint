from pathlib import Path

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# BASE_DIR = Path(__file__).parent.resolve()
# TESTDATA_DIR = BASE_DIR / 'testdata'


class CommonSettings(BaseSettings):
    """Общие настройки, для всех тестов."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    TEST_POSTGRES_PASSWORD: str = Field('', alias='TEST_POSTGRES_PASSWORD')
    TEST_POSTGRES_DB: str = Field('test_auth_db', alias='TEST_POSTGRES_DB')
    TEST_POSTGRES_USER: str = Field('postgres', alias='TEST_POSTGRES_USER')
    TEST_POSTGRES_HOST: str = Field('test-auth-db', alias='TEST_POSTGRES_HOST')
    TEST_POSTGRES_PORT: int = Field(5432, alias='TEST_POSTGRES_PORT')

    REDIS_HOST: str = Field('127.0.0.1', alias='REDIS_HOST')
    REDIS_PORT: int = Field(6379, alias='REDIS_PORT')


settings = CommonSettings()
