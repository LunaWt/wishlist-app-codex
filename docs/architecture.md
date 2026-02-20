# Social Wishlist — архитектура (v2)

## 1) Цель и критерии готовности

**Цель:** дать пользователю готовый продукт для создания и публикации вишлистов с приватными резервами/вкладами и realtime-обновлениями.

**Готово, если:**
- есть email/password + Google OAuth,
- публичный просмотр работает без логина,
- резервы/вклады доступны через guest-session,
- владелец видит только агрегаты (без персоналий),
- realtime работает без ручного refresh,
- UI адаптивный и production-like,
- проект запускается через Docker и проходит тесты.

---

## 2) Роли и доступ

| Действие | Anonymous | Guest session | Owner |
|---|---:|---:|---:|
| Смотреть опубликованный список | ✅ | ✅ | ✅ |
| Резервировать single-item | ❌ | ✅ | ❌ |
| Вносить вклад в group-item | ❌ | ✅ | ❌ |
| Создавать/редактировать список | ❌ | ❌ | ✅ |
| Публиковать/закрывать список | ❌ | ❌ | ✅ |
| Видеть, кто именно внёс/зарезервировал | ❌ | Только свои действия | ❌ |

---

## 3) Архитектурная схема (C4-lite)

### Контейнеры
- **Web:** Next.js 16 (App Router, TypeScript, Tailwind).
- **API:** FastAPI + SQLAlchemy async + Alembic.
- **DB:** PostgreSQL (local Docker, prod Neon).
- **OAuth:** Google.

### Ключевые backend-компоненты
- `auth`: регистрация, логин, JWT cookie, OAuth.
- `wishlists`: owner CRUD и управление жизненным циклом списка.
- `public`: guest-session, резервы, вклады.
- `realtime`: WS-канал + журнал событий.
- `preview`: автопарсинг URL (Ozon/WB + общий fallback), cache, SSRF guard.

---

## 4) Модель данных

Таблицы:
- `users`
- `oauth_accounts`
- `wishlists`
- `wishlist_items`
- `guest_sessions`
- `reservations`
- `contributions`
- `realtime_events`
- `link_previews`

Важные правила:
- `wishlists.share_slug` — уникальный.
- `reservations.item_id` — один активный резерв на single-item.
- денежные значения — `Numeric(12,2)`.
- `collected_amount` меняется транзакционно.
- `occasion/event_date` удалены физически (v2).

---

## 5) API-контракты

Префикс: `/api/v1`

### Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/google/start`
- `GET /auth/google/callback`

### Owner
- `POST /wishlists`
- `GET /wishlists/mine`
- `GET /wishlists/{id}`
- `PATCH /wishlists/{id}`
- `POST /wishlists/{id}/publish`
- `POST /wishlists/{id}/close`
- `POST /wishlists/{id}/items`
- `PATCH /wishlists/{id}/items/{item_id}`
- `POST /wishlists/{id}/items/{item_id}/archive`
- `POST /wishlists/{id}/items/reorder`

### Public
- `GET /public/w/{share_slug}`
- `POST /public/w/{share_slug}/guest-session`
- `POST /public/w/{share_slug}/items/{item_id}/reserve`
- `DELETE /public/w/{share_slug}/items/{item_id}/reserve`
- `POST /public/w/{share_slug}/items/{item_id}/contributions`
- `GET /public/w/{share_slug}/events?cursor=...`
- `WS /ws/public/w/{share_slug}`

### Utility
- `POST /items/preview`

---

## 6) Приватность (критично)

**Owner view:**
- видит: `is_reserved`, `collected_amount`, `target_amount`, `progress_percent`.
- не видит: guest identity, индивидуальные суммы и метаданные гостя.

**Guest view:**
- видит: `reserved_by_you`, `my_contribution`, публичные агрегаты.

---

## 7) Realtime

- Канал: `WS /api/v1/ws/public/w/{share_slug}`
- События: `item_reserved`, `item_unreserved`, `contribution_added`, `item_updated`, `item_archived`, `wishlist_published`, `wishlist_closed`.
- При разрыве: reconnect + sync через `events?cursor`/refetch.

---

## 8) Edge-cases

1. Гонка резерва: первый коммит выигрывает, второй получает 409.
2. Переполнение сбора: принимается только остаток до target.
3. Удаление с активностью: только soft-archive.
4. Битая ссылка товара: fallback на ручной ввод.
5. Owner открывает public URL: owner-safe режим.
6. Закрытый список: новые резервы/вклады запрещены.

---

## 9) Безопасность

- JWT в httpOnly cookie.
- CORS ограничен разрешёнными origin.
- Валидация входа: Pydantic + frontend validation.
- SSRF guard в preview:
  - только http/https,
  - блок private/loopback/link-local/reserved адресов,
  - контролируемые таймауты.

---

## 10) Тест-стратегия

- **Backend:** pytest (core flow + preview Ozon/WB/fallback).
- **Frontend:** Vitest (auth autofill attrs, dashboard 3-field form и защита ручного ввода).
- **E2E:** Playwright smoke.
- **CI gates:** lint + tests + build.

---

## 11) Deployment topology

- **Web:** Vercel (`apps/web`)
- **API:** Render (Docker)
- **DB:** Neon PostgreSQL

Минимальные env:
- API: `DATABASE_URL`, `SECRET_KEY`, `SESSION_SECRET`, `FRONTEND_URL`, `CORS_ORIGINS`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- Web: `NEXT_PUBLIC_API_URL`

Rollback:
- Vercel — previous deployment,
- Render — previous revision,
- DB — Alembic downgrade (по необходимости).
