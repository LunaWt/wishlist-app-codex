# Social Wishlist — Architecture

## 1. Product goals and readiness criteria

### Goals
- Let owners create themed wishlists and share public links.
- Let friends reserve gifts or contribute to expensive gifts together.
- Preserve surprise: owner sees aggregate state only, never identities or personal contribution amounts.
- Update all open sessions in realtime.

### Ready-for-demo criteria
- Auth (email/password + Google OAuth) works.
- Public link works without registration.
- Reserve and contribution flows work with race-condition guards.
- Realtime updates visible without refresh.
- Mobile layout is usable (360px).

---

## 2. Roles and permission matrix

| Action | Anonymous | Guest session | Owner |
|---|---|---|---|
| Open published wishlist link | ? | ? | ? |
| Reserve single gift | ? | ? | ? (owner flow disabled) |
| Contribute to group gift | ? | ? | ? (owner flow disabled) |
| Create/edit wishlist | ? | ? | ? |
| Publish/close wishlist | ? | ? | ? |
| See who reserved/contributed | ? | ? | ? |

---

## 3. Main use cases

### Owner
1. Register/login.
2. Create wishlist.
3. Add items (single or group mode).
4. Publish list -> receives share slug.
5. Observe aggregate status in realtime.

### Guest
1. Open public link without account.
2. Start guest session with a display name.
3. Reserve single item OR contribute to group item.
4. Receive realtime updates when others act.

### Anonymous
1. Open link and browse.
2. Must create guest session before reserve/contribution.

---

## 4. C4-lite overview

### Context
- **Web client (Next.js)**
- **API (FastAPI)**
- **PostgreSQL**
- **OAuth provider (Google)**

### Containers
- Frontend deployed on Vercel.
- Backend deployed on Render.
- Managed Postgres on Neon.

### Key backend components
- Auth module (credentials + OAuth)
- Wishlist owner module
- Public module (guest actions)
- Realtime gateway (WebSocket)
- Link preview service (OpenGraph/JSON-LD parser + cache)

---

## 5. Data model (tables)

- `users`
- `oauth_accounts`
- `wishlists`
- `wishlist_items`
- `guest_sessions`
- `reservations`
- `contributions`
- `realtime_events`
- `link_previews`

### Important constraints
- `wishlists.share_slug` unique.
- `reservations.item_id` unique (single current reservation state per item).
- `wishlist_items.collected_amount` maintained transactionally.

---

## 6. API contracts

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

## 7. Realtime protocol

### Event shape
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

### Reconnect strategy
- Client reconnects automatically after disconnect.
- Client refetches wishlist query.
- Optional event cursor API can backfill missed updates.

---

## 8. Privacy and security

### Privacy guarantees
- Owner item view includes only aggregate fields (`is_reserved`, `collected_amount`, progress).
- Identity and per-person contribution values are never returned in owner responses.

### Security
- JWT access + refresh in httpOnly cookies.
- Google OAuth via Authlib.
- CORS restricted by env.
- Link preview endpoint blocks non-http(s), localhost and private IP ranges (SSRF guard).
- Input validation via Pydantic / Zod.

---

## 9. Edge-case behavior

1. Reservation race -> row lock + conflict response.
2. Contribution overflow -> accepted amount is capped to remaining target.
3. Item with historical commitments -> soft archive only.
4. Broken product URL -> manual entry still available.
5. Owner opening public link -> owner view, not guest flow.
6. Closed wishlist -> no new reserve/contribution actions.

---

## 10. Non-functional requirements

- Mobile-first responsive UI.
- Realtime perceived latency target: <1s in normal conditions.
- Stable API schema with generated shared types.
- CI runs lint/test/build gates.

---

## 11. Test strategy

### Backend
- pytest async flow test for auth + publish + reserve + contribution.

### Frontend
- Vitest unit test (utilities).
- Playwright smoke test for landing page.

### Acceptance checks
- End-to-end manual flow from owner creation to guest actions and realtime updates.

---

## 12. Deployment topology and env vars

### Environments
- **Vercel**: Next.js app (`apps/web`)
- **Render**: FastAPI container (`apps/api`)
- **Neon**: Postgres DB

### Key env vars
- API: `DATABASE_URL`, `SECRET_KEY`, `SESSION_SECRET`, `FRONTEND_URL`, `CORS_ORIGINS`, OAuth vars
- Web: `NEXT_PUBLIC_API_URL`

### Rollback
- Vercel: revert to previous deployment.
- Render: rollback to previous service revision.
- DB schema rollback via Alembic downgrade (if needed and safe).

---

## 13. Risks and mitigations

1. **OAuth credentials missing** -> credentials auth remains fully operational.
2. **Network instability for WebSockets** -> reconnect + REST refetch fallback.
3. **Parsing variance in link preview** -> graceful partial metadata + manual edit.
4. **Concurrency bugs** -> row-level locks and conflict handling in critical mutations.
