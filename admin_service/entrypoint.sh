#!/bin/sh
set -e

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

exec uwsgi --strict --ini uwsgi.ini
