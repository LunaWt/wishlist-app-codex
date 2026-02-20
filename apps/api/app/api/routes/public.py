from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DbSession, OptionalGuestSession, OptionalUser
from app.core.config import get_settings
from app.core.security import create_guest_token
from app.models.contribution import Contribution
from app.models.enums import EventType, ItemMode, ItemStatus, WishlistStatus
from app.models.guest_session import GuestSession
from app.models.realtime_event import RealtimeEvent
from app.models.reservation import Reservation
from app.models.wishlist_item import WishlistItem
from app.schemas.public import (
    ContributionRequest,
    ContributionResponse,
    EventsResponse,
    GuestSessionCreateRequest,
    GuestSessionResponse,
    ReservationResponse,
)
from app.schemas.wishlist import PublicWishlistView
from app.services.event_service import publish_event
from app.services.wishlist_service import (
    build_guest_item_view,
    build_owner_item_view,
    calculate_progress,
    get_public_wishlist_or_404,
)

router = APIRouter(prefix='/public', tags=['public'])



def _validate_guest_session_for_wishlist(
    guest_session: GuestSession | None,
    wishlist_id: UUID,
) -> GuestSession | None:
    if not guest_session:
        return None
    if guest_session.wishlist_id != wishlist_id:
        return None
    expires_at = guest_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        return None
    return guest_session


@router.get('/w/{share_slug}', response_model=PublicWishlistView)
async def get_public_wishlist(
    share_slug: str,
    db: DbSession,
    user: OptionalUser,
    guest_session: OptionalGuestSession,
) -> PublicWishlistView:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)
    guest_session = _validate_guest_session_for_wishlist(guest_session, wishlist.id)

    if user and user.id == wishlist.owner_id:
        viewer_kind = 'owner'
        items = [build_owner_item_view(item) for item in wishlist.items if item.status != ItemStatus.ARCHIVED]
    else:
        viewer_kind = 'guest' if guest_session else 'anonymous'
        items = [
            build_guest_item_view(item, guest_session)
            for item in wishlist.items
            if item.status != ItemStatus.ARCHIVED
        ]

    return PublicWishlistView(
        id=wishlist.id,
        title=wishlist.title,
        description=wishlist.description,
        currency=wishlist.currency,
        status=wishlist.status,
        share_slug=wishlist.share_slug or share_slug,
        viewer_kind=viewer_kind,
        items=items,
    )


@router.post('/w/{share_slug}/guest-session', response_model=GuestSessionResponse)
async def create_guest_session(
    share_slug: str,
    payload: GuestSessionCreateRequest,
    db: DbSession,
) -> GuestSessionResponse:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)
    settings = get_settings()

    expires_at = datetime.now(UTC) + timedelta(days=settings.guest_token_ttl_days)
    session = GuestSession(
        wishlist_id=wishlist.id,
        display_name=payload.name,
        expires_at=expires_at,
        is_active=True,
        last_seen_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()

    token = create_guest_token(
        guest_session_id=str(session.id),
        wishlist_id=str(wishlist.id),
        expires_days=settings.guest_token_ttl_days,
    )

    await db.commit()
    await db.refresh(session)

    return GuestSessionResponse(
        token=token,
        guest_session_id=session.id,
        guest_name=session.display_name,
        expires_at=session.expires_at,
    )


@router.post('/w/{share_slug}/items/{item_id}/reserve', response_model=ReservationResponse)
async def reserve_item(
    share_slug: str,
    item_id: UUID,
    db: DbSession,
    guest_session: OptionalGuestSession,
) -> ReservationResponse:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)
    guest_session = _validate_guest_session_for_wishlist(guest_session, wishlist.id)
    if not guest_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Guest session is required')

    if wishlist.status == WishlistStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Wishlist is closed')

    item = next((i for i in wishlist.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')

    if item.mode != ItemMode.SINGLE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Only reservation is allowed for this item')
    if item.status != ItemStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Item is not active')

    lock_result = await db.execute(select(Reservation).where(Reservation.item_id == item_id).with_for_update())
    reservation = lock_result.scalar_one_or_none()

    if reservation and reservation.is_active and reservation.guest_session_id != guest_session.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Item is already reserved')

    now = datetime.now(UTC)
    if reservation:
        reservation.guest_session_id = guest_session.id
        reservation.is_active = True
        reservation.reserved_at = now
        reservation.released_at = None
    else:
        db.add(
            Reservation(
                item_id=item.id,
                guest_session_id=guest_session.id,
                is_active=True,
                reserved_at=now,
                released_at=None,
            )
        )

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_RESERVED,
        item_id=item.id,
        payload={'item_id': str(item.id), 'is_reserved': True},
    )
    await db.commit()

    return ReservationResponse(message='Item reserved', item_id=item.id, is_reserved=True)


@router.delete('/w/{share_slug}/items/{item_id}/reserve', response_model=ReservationResponse)
async def unreserve_item(
    share_slug: str,
    item_id: UUID,
    db: DbSession,
    guest_session: OptionalGuestSession,
) -> ReservationResponse:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)
    guest_session = _validate_guest_session_for_wishlist(guest_session, wishlist.id)
    if not guest_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Guest session is required')

    result = await db.execute(select(Reservation).where(Reservation.item_id == item_id).with_for_update())
    reservation = result.scalar_one_or_none()
    if not reservation or not reservation.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Reservation not found')

    if reservation.guest_session_id != guest_session.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You can release only your reservation')

    reservation.is_active = False
    reservation.released_at = datetime.now(UTC)

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_UNRESERVED,
        item_id=item_id,
        payload={'item_id': str(item_id), 'is_reserved': False},
    )
    await db.commit()

    return ReservationResponse(message='Reservation released', item_id=item_id, is_reserved=False)


@router.post('/w/{share_slug}/items/{item_id}/contributions', response_model=ContributionResponse)
async def contribute_to_item(
    share_slug: str,
    item_id: UUID,
    payload: ContributionRequest,
    db: DbSession,
    guest_session: OptionalGuestSession,
) -> ContributionResponse:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)
    guest_session = _validate_guest_session_for_wishlist(guest_session, wishlist.id)
    if not guest_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Guest session is required')

    if wishlist.status == WishlistStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Wishlist is closed')

    item = next((i for i in wishlist.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')

    if item.mode != ItemMode.GROUP:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Only contributions are allowed for this item')
    if item.status != ItemStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Item is not active')

    locked_item_result = await db.execute(
        select(WishlistItem).where(WishlistItem.id == item.id).with_for_update()
    )
    locked_item = locked_item_result.scalar_one()

    target = locked_item.target_amount or locked_item.price
    if not target or target <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Target amount is not set')

    remaining = target - locked_item.collected_amount
    if remaining <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Collection already completed')

    requested = payload.amount
    accepted = min(requested, remaining)
    if accepted <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Minimum contribution is 1')

    db.add(
        Contribution(
            item_id=locked_item.id,
            guest_session_id=guest_session.id,
            amount=accepted,
            currency=wishlist.currency,
        )
    )

    locked_item.collected_amount = (locked_item.collected_amount or Decimal('0')) + accepted
    progress = calculate_progress(locked_item.collected_amount, locked_item.target_amount, locked_item.price)

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.CONTRIBUTION_ADDED,
        item_id=locked_item.id,
        payload={
            'item_id': str(locked_item.id),
            'accepted_amount': str(accepted),
            'collected_amount': str(locked_item.collected_amount),
            'progress_percent': progress,
        },
    )
    await db.commit()

    message = 'Contribution added'
    if accepted < requested:
        message = f'Only {accepted} was accepted (target reached)'

    return ContributionResponse(
        message=message,
        item_id=locked_item.id,
        accepted_amount=accepted,
        collected_amount=locked_item.collected_amount,
        progress_percent=progress,
    )


@router.get('/w/{share_slug}/events', response_model=EventsResponse)
async def get_events(
    share_slug: str,
    db: DbSession,
    cursor: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> EventsResponse:
    wishlist = await get_public_wishlist_or_404(db=db, slug=share_slug)

    stmt = select(RealtimeEvent).where(RealtimeEvent.wishlist_id == wishlist.id)
    if cursor is not None:
        stmt = stmt.where(RealtimeEvent.id > cursor)

    stmt = stmt.order_by(RealtimeEvent.id.asc()).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()

    next_cursor = events[-1].id if events else cursor

    return EventsResponse(
        events=[
            {
                'id': event.id,
                'event_type': event.event_type,
                'item_id': event.item_id,
                'payload': event.payload,
                'created_at': event.created_at,
            }
            for event in events
        ],
        next_cursor=next_cursor,
    )
