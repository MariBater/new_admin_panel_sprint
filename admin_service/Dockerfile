FROM python:3.10-slim AS base

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- Этап сборки зависимостей ---
FROM base AS builder

COPY requirements.txt .

# Устанавливаем сборочные зависимости, необходимые для uWSGI
RUN apt-get update && apt-get install -y --no-install-recommends build-essential python3-dev

# Обновляем pip и собираем "колеса" зависимостей
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir /opt/app/wheels -r requirements.txt

# --- Финальный этап для продакшена ---
FROM base AS final

ENV DJANGO_SETTINGS_MODULE 'core.settings'

# Добавляем локальную bin-директорию пользователя в PATH
ENV PATH=/home/www-data/.local/bin:$PATH

# Устанавливаем libexpat1, необходимую для uWSGI в рантайме, и очищаем кэш apt
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя, группу и директории
# Создаем группу и пользователя, только если они не существуют
RUN (getent group www-data || groupadd -r www-data) \
    && (getent passwd www-data && usermod -d /home/www-data www-data || useradd --no-log-init -r -g www-data --home-dir /home/www-data --create-home www-data) \
    && mkdir -p /home/www-data /data/static /data/media /opt/app/static \
    && chown -R www-data:www-data /home/www-data /data /opt/app/static

# Копируем собранные зависимости, код приложения и entrypoint
COPY --from=builder /opt/app/wheels /wheels
COPY --from=builder /opt/app/requirements.txt .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY . .

EXPOSE 8000

# Переключаемся на непривилегированного пользователя
USER www-data

# Устанавливаем зависимости от имени пользователя
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt

# Собираем статические файлы от имени пользователя www-data.
# Django поместит их в директорию, указанную в STATIC_ROOT.
RUN python manage.py collectstatic --noinput

ENTRYPOINT ["/entrypoint.sh"]