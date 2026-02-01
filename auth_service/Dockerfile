FROM python:3.11-slim-bullseye as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Этап сборки зависимостей ---

COPY auth_service/requirements.txt .

# Разделяем команды для стабильности и кэширования
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Финальный этап для продакшена ---
FROM python:3.11-slim-bullseye AS final

# Добавляем локальную bin-директорию пользователя в PATH, чтобы находить alembic и другие утилиты
ENV PATH=/home/appuser/.local/bin:$PATH

# Создаем пользователя без root-прав для безопасности
RUN useradd --create-home appuser 

WORKDIR /app

# Копируем файлы и устанавливаем зависимости от имени root
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt /app/requirements.txt
COPY auth_service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY auth_service/alembic.ini /app/alembic.ini
COPY auth_service/alembic/ /app/alembic/
COPY auth_service/src/db/ /app/db/
COPY auth_service/src/ /app/src/

# Устанавливаем зависимости от имени пользователя, чтобы они попали в его домашнюю директорию
USER appuser
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /app/requirements.txt

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001", "--timeout", "120"]