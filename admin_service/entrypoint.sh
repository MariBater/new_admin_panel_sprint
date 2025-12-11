#!/bin/sh
set -e

python manage.py migrate --noinput

python manage.py collectstatic --noinput --clear --verbosity 2

python - <<PYTHON
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")

if not (username and password and email):
    print("Superuser variables not set. Skipping creation.")
else:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created with email '{email}'.")
    else:
        print(f"Superuser '{username}' already exists.")
PYTHON

exec uwsgi --strict --ini uwsgi.ini
