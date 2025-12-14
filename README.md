https://github.com/eevtmn/online_cinema_service

Для запуска из корня проекта:
    docker-compose up -d --build     
После первого запуска выполнить
    docker-compose exec auth-service python /app/src/db/pg_superuser_cli.py admin 123 admin@gmail.com   


API сервиса онлайн-кинотеатра:
    http://127.0.0.1:81/content/api/openapi

API сервиса авторизации:
    http://127.0.0.1:81/auth/api/openapi

Админка django:
    http://127.0.0.1:81/admin/