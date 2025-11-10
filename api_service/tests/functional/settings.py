from pydantic import Field
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):

    es_host: str = Field(
        'http://elasticsearch:9200',
        alias='ELASTIC_HOST',
    )

    redis_host: str = Field('redis', alias='REDIS_HOST')
    redis_port: int = Field(6379, alias='REDIS_PORT')
    service_url: str = Field('http://api-service:8000', alias='SERVICE_API')


test_settings = TestSettings()
