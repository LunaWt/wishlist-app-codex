# tasks.md - Social Wishlist implementation checklist

> Правило: задачи выполняются строго по порядку.

## Task 1 - Bootstrap и foundation
- [x] Инициализирована монорепо структура (`apps`, `packages`, `docs`, `infra`).
- [x] Поднят базовый каркас FastAPI и Next.js.
- [x] Настроены базовые конфиги (lint/format/scripts).

## Task 2 - Backend core + Auth
- [x] FastAPI app factory + healthcheck.
- [x] SQLAlchemy async + Alembic.
- [x] Email/password auth (register/login/me/logout/refresh).
- [x] Google OAuth endpoints (start/callback).

## Task 3 - Owner domain API
- [x] CRUD wishlist/items для владельца.
- [x] Publish/close lifecycle.
- [x] Owner-safe представление товаров (без раскрытия персональных данных).

## Task 4 - Public access + guest session
- [x] Публичный доступ по `share_slug`.
- [x] Создание guest-session.
- [x] Разделение режимов anonymous/guest/owner.

## Task 5 - Reservations & Contributions
- [x] Резерв/снятие резерва single-item.
- [x] Вклады в group-item с агрегированным прогрессом.
- [x] Транзакционные защиты от гонок и oversubscribe.
- [x] Soft-archive для товаров с историей.

## Task 6 - Realtime
- [x] WebSocket-канал по wishlist slug.
- [x] Event persistence (`realtime_events`) и broadcast.
- [x] Fallback API (`events?cursor`).

## Task 7 - URL Autofill
- [x] Endpoint `/items/preview`.
- [x] Парсинг OpenGraph/JSON-LD.
- [x] Кэш `link_previews` + SSRF guard.

## Task 8 - Frontend UX/UI
- [x] Страницы: landing/auth/dashboard/public.
- [x] Реалтайм обновления в UI.
- [x] UX для guest-session и URL autofill.
- [x] Адаптивный mobile-first интерфейс.

## Task 9 - Testing & stabilization
- [x] Backend pytest integration flow.
- [x] Frontend vitest unit test.
- [x] Frontend playwright smoke e2e.
- [x] Локально пройдены lint + tests + build.

## Task 10 - Docker, CI/CD, deploy, submission assets
- [x] Dockerfiles + docker-compose (локальный full stack поднимается).
- [x] CI workflow scaffold.
- [x] Подготовлены docs: architecture/product decisions/demo script/AI worklog.
- [ ] Production deploy (Vercel/Render/Neon) - требует подключения прод-аккаунтов и секретов.
- [ ] Финальная запись экран-демо 3-5 минут - выполняется вручную перед отправкой.
