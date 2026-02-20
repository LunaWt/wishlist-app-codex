# Social Wishlist - архитектура (v1)

## 1. Цель продукта и критерии готовности

### Цель
Дать пользователю возможность:
- создавать вишлисты (повод, дата, описание);
- делиться публичной ссылкой без регистрации получателя;
- избегать дублирующихся подарков через резерв;
- собирать совместные подарки через вклады;
- сохранять сюрприз (владелец не видит, кто и сколько внёс).

### Definition of Done (готово к сдаче)
- Email/пароль auth + Google OAuth работают.
- Публичная ссылка работает без логина.
- Резерв и вклады работают транзакционно.
- Realtime-обновления приходят без перезагрузки.
- Владелец видит только агрегаты, без персоналий.
- UI адаптивен на мобильных (минимум 360px).
- Есть Docker, CI, README, документы для сдачи.

---

## 2. Роли и матрица прав

| Действие | Anonymous | Guest Session | Owner |
|---|---:|---:|---:|
| Смотреть опубликованный вишлист | ✅ | ✅ | ✅ |
| Резервировать single-item | ❌ | ✅ | ❌ |
| Вносить вклад в group-item | ❌ | ✅ | ❌ |
| Создавать/редактировать список | ❌ | ❌ | ✅ |
| Публиковать/закрывать список | ❌ | ❌ | ✅ |
| Видеть, кто внёс/зарезервировал | ❌ | Только себя | ❌ |

> Владелец никогда не получает идентифицирующие данные гостей в API/UI.

---

## 3. Основные пользовательские сценарии

### Owner flow
1. Регистрация/логин.
2. Создание списка.
3. Добавление товаров (`single` или `group`).
4. Публикация списка и получение `share_slug`.
5. Наблюдение за статусами/прогрессом в realtime.

### Guest flow
1. Открытие публичной ссылки.
2. Создание guest-session (имя + токен сессии).
3. Резерв single-товара или вклад в group-товар.
4. Получение realtime обновлений.

### Anonymous flow
1. Может просматривать.
2. Для действий должен создать guest-session.

---

## 4. C4-lite: контекст и контейнеры

## 4.1 Context
- **Web client**: Next.js.
- **API**: FastAPI.
- **DB**: PostgreSQL.
- **OAuth provider**: Google.

## 4.2 Containers
- Frontend: Vercel (цель deploy).
- Backend: Render (Docker image).
- PostgreSQL: Neon (prod), Postgres в Docker (local).

## 4.3 Backend компоненты
- `auth` - credentials + OAuth + cookie-based session.
- `wishlists` - owner CRUD и lifecycle.
- `public` - публичные read/write действия через guest-session.
- `realtime` - WebSocket и event-log.
- `preview` - парсинг метаданных URL + cache + SSRF guard.

---

## 5. Технологический стек

### Frontend
- Next.js 16 (App Router, TypeScript)
- TailwindCSS
- React Query
- react-hook-form + zod
- WebSocket клиент + fallback polling/events

### Backend
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- Pydantic v2
- authlib (Google OAuth)
- passlib (password hashing)

### Infra/Quality
- Docker / docker-compose
- GitHub Actions CI
- Pytest + Vitest + Playwright

---

## 6. Модель данных

## 6.1 Таблицы
- `users`
- `oauth_accounts`
- `wishlists`
- `wishlist_items`
- `guest_sessions`
- `reservations`
- `contributions`
- `realtime_events`
- `link_previews`

## 6.2 Важные ограничения
- `wishlists.share_slug` - unique.
- `reservations.item_id` - unique (один активный резерв на single-item).
- Денежные поля - `Numeric(12,2)`.
- `wishlist_items.collected_amount` изменяется транзакционно.

## 6.3 Enum/статусы
- `wishlist_status`: `draft | published | closed`
- `item_mode`: `single | group`
- `item_status`: `active | archived | unavailable`
- `event_type`: `item_reserved | item_unreserved | contribution_added | item_updated | item_archived | wishlist_published | wishlist_closed`

---

## 7. API-контракты

Все endpoints под префиксом: `/api/v1`

## 7.1 Auth
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `GET /auth/google/start`
- `GET /auth/google/callback`

## 7.2 Owner API
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

## 7.3 Public API
- `GET /public/w/{share_slug}`
- `POST /public/w/{share_slug}/guest-session`
- `POST /public/w/{share_slug}/items/{item_id}/reserve`
- `DELETE /public/w/{share_slug}/items/{item_id}/reserve`
- `POST /public/w/{share_slug}/items/{item_id}/contributions`
- `GET /public/w/{share_slug}/events?cursor=...`
- `WS /ws/public/w/{share_slug}`

## 7.4 Utility API
- `POST /items/preview`

---

## 8. Контракт приватности (критично)

### Owner view
Получает только:
- `is_reserved`
- `collected_amount`
- `target_amount`
- `progress_percent`

Не получает:
- guest identity
- individual contribution amounts
- guest/session metadata

### Guest view
Получает:
- `reserved_by_you`
- `my_contribution`
- публичные агрегаты item статуса

---

## 9. Realtime протокол

## 9.1 Канал
- `WS /api/v1/ws/public/w/{share_slug}`

## 9.2 Событие
```json
{
  "id": 120,
  "event_type": "contribution_added",
  "item_id": "uuid",
  "payload": {
    "item_id": "uuid",
    "collected_amount": "4000.00",
    "progress_percent": 40
  },
  "created_at": "2026-02-20T12:34:56Z"
}
```

## 9.3 Потеря соединения
- клиент делает auto-reconnect;
- после reconnect обновляет данные через обычный fetch;
- при необходимости читает пропущенные события через cursor endpoint.

---

## 10. Политика edge-cases

1. **Race reserve**: первый коммит побеждает, второй получает 409.
2. **Oversubscribe**: вклад ограничивается остатком до target.
3. **Удаление товара с активностью**: только soft-archive.
4. **Сломанный URL preview**: fallback на ручное заполнение.
5. **Owner открывает public URL**: owner-safe режим.
6. **Закрытый wishlist**: нельзя новые резервы/вклады.
7. **Недособранная сумма**: `partially funded` (pledge only, без платежей).

---

## 11. Безопасность

- JWT access/refresh в httpOnly cookies.
- CORS ограничивается `CORS_ORIGINS`.
- Валидация входа на backend (Pydantic) и frontend (zod).
- SSRF guard в URL preview:
  - запрет `file://`, `ftp://`, локальных/приватных сетей и localhost.
- Ограничения ролей в каждом endpoint.

---

## 12. Нефункциональные требования

- Mobile-first верстка.
- Realtime UX latency target: < 1 сек в нормальной сети.
- Предсказуемая сборка через Docker.
- Повторяемость запуска через README.

---

## 13. Тестовая стратегия

### Backend
- `pytest` интеграционный сценарий:
  - register/login
  - create/publish wishlist
  - guest session
  - reserve + contribution
  - owner privacy response

### Frontend
- `vitest` unit тест утилит.
- `playwright` smoke e2e.

### CI gates
- lint
- tests
- build

---

## 14. Deployment topology и rollback

## 14.1 Topology
- Web -> Vercel (`apps/web`)
- API -> Render (`infra/docker/api.Dockerfile`)
- DB -> Neon PostgreSQL

## 14.2 Environment variables
- API:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `SESSION_SECRET`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `REFRESH_TOKEN_EXPIRE_DAYS`
  - `FRONTEND_URL`
  - `CORS_ORIGINS`
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `GOOGLE_REDIRECT_URI`
- WEB:
  - `NEXT_PUBLIC_API_URL`

## 14.3 Rollback
- Vercel: rollback на предыдущий deploy.
- Render: rollback на предыдущую ревизию.
- DB: откат миграций Alembic (если безопасно).

---

## 15. Риски и mitigation

1. **Нет OAuth credentials**  
   Mitigation: credentials-auth работает независимо.
2. **Нестабильный WebSocket**  
   Mitigation: reconnect + refetch + events fallback.
3. **Низкое качество метаданных URL**  
   Mitigation: partial preview + ручное редактирование.
4. **Конкурентные гонки**  
   Mitigation: транзакции, lock/select-for-update, 409 handling.
