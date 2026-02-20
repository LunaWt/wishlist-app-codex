FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/README.md ./apps/api/
COPY apps/api/app ./apps/api/app
COPY apps/api/alembic ./apps/api/alembic
COPY apps/api/alembic.ini ./apps/api/alembic.ini

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ./apps/api

WORKDIR /app/apps/api

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
