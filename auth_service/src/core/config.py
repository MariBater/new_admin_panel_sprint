from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, computed_field


class Settings(BaseSettings):
    # Pydantic-settings автоматически загружает .env, load_dotenv() не нужен.
    # extra='ignore' предотвращает ошибку валидации, если в окружении есть
    # переменные, не определенные в этой модели (например, DATABASE_URL для Alembic).
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8', extra='ignore'
    )

    # Использование alias избыточно, когда имя поля совпадает с переменной окружения.
    PROJECT_NAME: str = 'auth-service'

    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379

    POSTGRES_PASSWORD: str = ''
    POSTGRES_DB: str = 'auth-db'
    POSTGRES_USER: str = 'postgres'
    POSTGRES_HOST: str = 'auth-db'
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def POSTGRES_DSN(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Настройки для JWT
    SECRET_KEY: str = "your_super_secret_key_for_tests"  # Убрано значение по умолчанию для безопасности
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Исправлена ошибка: alias был 'ACCESS_TOKEN_EXPIRE_MINUTES'
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    JAEGER_ENDPOINT: str = 'http://jaeger:4317'
    JAEGER_SERVICE_NAME: str = 'auth-service'
    TRACING_ENABLED: bool = True

    # Настройки для Yandex OAuth
    YANDEX_CLIENT_ID: str = ''
    YANDEX_CLIENT_SECRET: str = ''
    YANDEX_REDIRECT_URI: str = ''


settings = Settings()
