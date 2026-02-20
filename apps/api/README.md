# Wishlist API

## Run locally

```bash
uv sync --extra dev
cp .env.example .env
alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run tests

```bash
uv run pytest
```
