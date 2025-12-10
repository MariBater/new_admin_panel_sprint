FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH="/app"

COPY requirements.txt .

RUN  pip install --upgrade pip & pip install --no-cache-dir -r requirements.txt

COPY src/ src/

EXPOSE 8001

CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001", "--timeout", "120"]