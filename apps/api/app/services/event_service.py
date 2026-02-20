from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventType
from app.models.realtime_event import RealtimeEvent
from app.realtime.manager import connection_manager


async def publish_event(
    db: AsyncSession,
    *,
    wishlist_id: UUID,
    share_slug: str | None,
    event_type: EventType,
    payload: dict[str, Any],
    item_id: UUID | None = None,
) -> RealtimeEvent:
    event = RealtimeEvent(
        wishlist_id=wishlist_id,
        event_type=event_type,
        item_id=item_id,
        payload=payload,
    )
    db.add(event)
    await db.flush()

    if share_slug:
        await connection_manager.broadcast(
            share_slug,
            {
                'id': event.id,
                'event_type': event.event_type.value,
                'item_id': str(item_id) if item_id else None,
                'payload': payload,
                'created_at': event.created_at.isoformat() if event.created_at else None,
            },
        )

    return event
