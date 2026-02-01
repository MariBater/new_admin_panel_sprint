#!/bin/sh

# Этот скрипт является точкой входа для контейнера auth-service.
# Он гарантирует, что миграции базы данных будут применены перед запуском основного приложения.

# Выходим немедленно, если команда завершается с ошибкой.
set -e

# Ожидаем, пока база данных будет готова принимать подключения.
echo "Waiting for database..."
python - <<PYTHON
import os
import sys
import asyncio
import time
import asyncpg

user = os.environ.get('POSTGRES_USER')
password = os.environ.get('POSTGRES_PASSWORD')
host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT')
db = os.environ.get('POSTGRES_DB')
dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"

async def check_db():
    for _ in range(20):
        try:
            conn = await asyncpg.connect(dsn)
            await conn.close()
            return
        except (asyncpg.PostgresError, OSError):
            await asyncio.sleep(1)
    sys.exit("Database not available.")

asyncio.run(check_db())
PYTHON

echo "Database is ready."

# Применяем миграции Alembic
alembic -c /app/alembic.ini upgrade head

# Запускаем команду, переданную в Dockerfile (CMD)
exec "$@"