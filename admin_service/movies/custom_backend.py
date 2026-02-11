import http
import json
import os
from pathlib import Path

import requests
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from jose import jwt
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

User = get_user_model()


class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        url = os.getenv('AUTH_SERVICE_API', '')
        if url == '':
            return

        response = requests.post(
            f'{url}/login', data=json.dumps({'login': username, 'password': password})
        )
        if response.status_code != http.HTTPStatus.OK:
            return None

        data = response.json()
        if not 'access_token' in data:
            return None

        payload = jwt.decode(
            data.get('access_token'),
            os.getenv('SECRET_KEY', ''),
            algorithms=[os.getenv('ALGORITHM', '')],
        )

        try:
            user, created = User.objects.get_or_create(
                auth_user_id=payload['user_id'],
            )
            if not 'admin' in payload.get('roles', ''):
                return None

            user.is_staff = True
            user.is_superuser = True
            user.email = payload.get('email', '')
            user.set_password(password)

            user.save()
        except Exception as e:
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
