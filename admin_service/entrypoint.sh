#!/bin/sh
set -e

# Ожидаем, пока база данных будет готова принимать подключения.
# DJANGO_SETTINGS_MODULE уже установлен в Dockerfile.
echo "Waiting for database..."
python - <<PYTHON
import os
import sys
import time
import psycopg

dsn = f"host={os.environ.get('POSTGRES_HOST')} port={os.environ.get('POSTGRES_PORT')} dbname={os.environ.get('POSTGRES_DB')} user={os.environ.get('POSTGRES_USER')} password={os.environ.get('POSTGRES_PASSWORD')}"

for _ in range(20):
    try:
        with psycopg.connect(dsn):
            break
    except psycopg.OperationalError:
        time.sleep(1)
else:
    sys.exit("Database not available.")
PYTHON

echo "Database is ready."

python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear --verbosity 2

python - <<PYTHON
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if not (email and password):
    print("Superuser variables not set. Skipping creation.")
else:
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            password=password
        )
        print(f"Superuser '{email}' created.")
    else:
        print(f"Superuser '{email}' already exists.")
PYTHON

# Указываем более вероятный путь к файлу конфигурации uwsgi
exec uwsgi --strict --ini uwsgi/uwsgi.ini
