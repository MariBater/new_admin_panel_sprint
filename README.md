https://github.com/eevtmn/online_cinema_service

Для запуска из корня проекта: `docker-compose up -d --build`

### Настройка окружения

Перед первым запуском создайте в корне проекта файл `.env` и добавьте в него необходимые переменные.

#### Учетные данные для базы данных
Эти переменные используются для инициализации баз данных и подключения к ним.

`POSTGRES_USER=postgres`
`POSTGRES_PASSWORD=your_strong_password`
`POSTGRES_DB=auth_db`

#### Учетные данные суперпользователя (для Django и Auth-сервиса)
`AUTH_SUPERUSER_LOGIN=admin`
`AUTH_SUPERUSER_PASSWORD=admin`
`AUTH_SUPERUSER_EMAIL=admin@example.com`
`DJANGO_SUPERUSER_EMAIL=admin@example.com`
`DJANGO_SUPERUSER_PASSWORD=admin`

#### Ключи для входа через Яндекс (Yandex OAuth)
`YANDEX_CLIENT_ID=640e58f11b72456b9db5dab0268477f2`
`YANDEX_CLIENT_SECRET=dc698f1bc82e4c76bf18bfd72d6a9c59`
`YANDEX_REDIRECT_URI=http://127.0.0.1:81/auth/api/v1/oauth/yandex/callback`

API сервиса онлайн-кинотеатра: http://127.0.0.1:81/content/api/openapi

API сервиса авторизации: http://127.0.0.1:81/auth/api/openapi

Админка django: http://127.0.0.1:81/admin/