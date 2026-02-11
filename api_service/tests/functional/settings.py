from pathlib import Path

from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.resolve()
TESTDATA_DIR = BASE_DIR / 'testdata'


class CommonSettings(BaseSettings):
    """Общие настройки, для всех тестов."""

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    es_host: str = Field(default='127.0.0.1', alias='ES_HOST')
    es_port: str = Field(default='9200', alias='ES_PORT')

    redis_host: str = Field(default='127.0.0.1', alias='REDIS_HOST')
    redis_port: str = Field(default='6379', alias='REDIS_PORT')
    redis_db: str = Field(default='0', alias='REDIS_DB')

    api_host: str = Field(default='127.0.0.1', alias='API_HOST')
    api_port: str = Field(default='81', alias='API_PORT')

    @property
    def es_url(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"

    @property
    def redis_conn_str(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def api_base_url(self) -> str:
        return f"http://{self.api_host}:{self.api_port}/api/v1"


class ESIndexSettings(BaseModel):
    """Модель настроек, для конкретного индекса."""

    index_name: str
    schema_file_path: Path
    data_file_path: Path


settings = CommonSettings()

film_index = ESIndexSettings(
    index_name='movies',
    schema_file_path=TESTDATA_DIR / 'es_schema_movies.json',
    data_file_path=TESTDATA_DIR / 'movies.json',
)

genre_index = ESIndexSettings(
    index_name='genres',
    schema_file_path=TESTDATA_DIR / 'es_schema_genres.json',
    data_file_path=TESTDATA_DIR / 'genres.json',
)

person_index = ESIndexSettings(
    index_name='persons',
    schema_file_path=TESTDATA_DIR / 'es_schema_persons.json',
    data_file_path=TESTDATA_DIR / 'persons.json',
)

indexes = [
    film_index,
    genre_index,
    person_index,
]
