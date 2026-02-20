from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.realtime_event import RealtimeEvent
from app.models.wishlist import Wishlist
from app.realtime.manager import connection_manager

router = APIRouter(tags=['ws'])


@router.websocket('/ws/public/w/{share_slug}')
async def wishlist_events_ws(
    websocket: WebSocket,
    share_slug: str,
    cursor: int | None = Query(default=None, ge=0),
) -> None:
    async with SessionLocal() as db:
        wishlist_result = await db.execute(select(Wishlist).where(Wishlist.share_slug == share_slug))
        wishlist = wishlist_result.scalar_one_or_none()

        if not wishlist or wishlist.status.value not in {'published', 'closed'}:
            await websocket.close(code=1008)
            return

        await connection_manager.connect(share_slug, websocket)

        if cursor is not None:
            result = await db.execute(
                select(RealtimeEvent)
                .where(RealtimeEvent.wishlist_id == wishlist.id, RealtimeEvent.id > cursor)
                .order_by(RealtimeEvent.id.asc())
                .limit(100)
            )
            events = result.scalars().all()
            for event in events:
                await websocket.send_json(
                    {
                        'id': event.id,
                        'event_type': event.event_type.value,
                        'item_id': str(event.item_id) if event.item_id else None,
                        'payload': event.payload,
                        'created_at': event.created_at.isoformat() if event.created_at else None,
                    }
                )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(share_slug, websocket)
