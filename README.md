# WishWave - Social Wishlist

Production-oriented test project: create wishlists, share public links, reserve gifts, contribute together, and receive realtime updates.

## Stack
- Frontend: Next.js (App Router, TypeScript, Tailwind)
- Backend: FastAPI, SQLAlchemy async, Alembic
- Database: PostgreSQL
- Realtime: WebSocket + event log
- Auth: Email/password + Google OAuth

## Monorepo structure

```text
apps/
  api/      # FastAPI backend
  web/      # Next.js frontend
packages/
  shared-types/
docs/
infra/
```

## Quick start (Docker)

1. Copy env template:

```bash
cp apps/api/.env.example apps/api/.env
```

2. Set secure values in `apps/api/.env` (`SECRET_KEY`, `SESSION_SECRET`).

3. Run stack:

```bash
docker compose up --build
```

4. Open:
- Web: http://localhost:3000
- API docs: http://localhost:8000/api/v1/docs

## Local development (without Docker)

### Backend

```bash
cd apps/api
uv sync --extra dev
cp .env.example .env
alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cp apps/web/.env.example apps/web/.env.local
npm install
npm run dev:web
```

## Main API groups

- Auth: `/api/v1/auth/*`
- Owner: `/api/v1/wishlists/*`
- Public: `/api/v1/public/w/{share_slug}/*`
- Realtime WS: `/api/v1/ws/public/w/{share_slug}`
- Link preview: `/api/v1/items/preview`

## Tests

### Backend

```bash
cd apps/api
uv run pytest
```

### Frontend unit

```bash
npm run test:web
```

### Frontend e2e (smoke)

```bash
npm run test:e2e
```

## Deployment target

- Frontend: Vercel (`apps/web`)
- Backend: Render (Dockerfile: `infra/docker/api.Dockerfile`)
- Database: Neon PostgreSQL

Config templates:
- `infra/render/render.yaml`
- `infra/vercel/vercel.json`

## Submission artifacts

See:
- `docs/product-decisions.md`
- `docs/demo-script.md`
- `docs/ai-worklog.md`
- `docs/architecture.md`
