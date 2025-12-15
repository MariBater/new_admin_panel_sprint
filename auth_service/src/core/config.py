from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=f'.env', env_file_encoding='utf-8')

    PROJECT_NAME: str = Field('auth-service', alias='PROJECT_NAME')

    REDIS_HOST: str = Field('127.0.0.1', alias='REDIS_HOST')
    REDIS_PORT: int = Field(6379, alias='REDIS_PORT')

    POSTGRES_PASSWORD: str = Field('', alias='POSTGRES_PASSWORD')
    POSTGRES_DB: str = Field('auth-db', alias='POSTGRES_DB')
    POSTGRES_USER: str = Field('postgres', alias='POSTGRES_USER')
    POSTGRES_HOST: str = Field('auth-db', alias='POSTGRES_HOST')
    POSTGRES_PORT: int = Field(5432, alias='POSTGRES_PORT')

    # Настройки для JWT
    SECRET_KEY: str = Field(
        'your-super-secret-key-for-auth-service', alias='SECRET_KEY'
    )
    ALGORITHM: str = Field("HS256", alias='ALGORITHM')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, alias='ACCESS_TOKEN_EXPIRE_MINUTES')

    JAEGER_ENDPOINT: str = Field('http://jaeger:4317', alias='JAEGER_ENDPOINT')
    JAEGER_SERVICE_NAME: str = Field('', alias='JAEGER_SERVICE_NAME')


settings = Settings()
