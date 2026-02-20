from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contribution import Contribution
from app.models.guest_session import GuestSession
from app.models.reservation import Reservation
from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem


def _to_decimal(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal('0')


def calculate_progress(collected_amount: Decimal, target_amount: Decimal | None, price: Decimal | None) -> float:
    target = target_amount or price
    if not target or target <= 0:
        return 0.0
    return float(min((collected_amount / target) * 100, Decimal('100')))


def build_owner_item_view(item: WishlistItem) -> dict:
    reservation_active = bool(item.reservation and item.reservation.is_active)
    return {
        'id': item.id,
        'title': item.title,
        'product_url': item.product_url,
        'image_url': item.image_url,
        'notes': item.notes,
        'price': item.price,
        'mode': item.mode,
        'target_amount': item.target_amount,
        'collected_amount': item.collected_amount,
        'status': item.status,
        'position': item.position,
        'is_reserved': reservation_active,
        'progress_percent': calculate_progress(item.collected_amount, item.target_amount, item.price),
    }


def build_guest_item_view(item: WishlistItem, guest_session: GuestSession | None) -> dict:
    reserved_by_you = False
    if item.reservation and item.reservation.is_active and guest_session:
        reserved_by_you = item.reservation.guest_session_id == guest_session.id

    my_contribution = Decimal('0')
    if guest_session:
        for contribution in item.contributions:
            if contribution.guest_session_id == guest_session.id:
                my_contribution += contribution.amount

    return {
        'id': item.id,
        'title': item.title,
        'product_url': item.product_url,
        'image_url': item.image_url,
        'notes': item.notes,
        'price': item.price,
        'mode': item.mode,
        'target_amount': item.target_amount,
        'collected_amount': item.collected_amount,
        'status': item.status,
        'position': item.position,
        'is_reserved': bool(item.reservation and item.reservation.is_active),
        'reserved_by_you': reserved_by_you,
        'my_contribution': my_contribution,
        'progress_percent': calculate_progress(item.collected_amount, item.target_amount, item.price),
    }


async def get_owner_wishlist_or_404(
    db: AsyncSession,
    wishlist_id: UUID,
    owner_id: UUID,
) -> Wishlist:
    result = await db.execute(
        select(Wishlist)
        .options(
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.reservation),
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.contributions),
        )
        .where(Wishlist.id == wishlist_id, Wishlist.owner_id == owner_id)
    )
    wishlist = result.scalar_one_or_none()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Wishlist not found')
    wishlist.items.sort(key=lambda item: item.position)
    return wishlist


async def get_public_wishlist_or_404(db: AsyncSession, slug: str) -> Wishlist:
    result = await db.execute(
        select(Wishlist)
        .options(
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.reservation),
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.contributions),
        )
        .where(Wishlist.share_slug == slug)
    )
    wishlist = result.scalar_one_or_none()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Public wishlist not found')

    if wishlist.status.value not in {'published', 'closed'}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Wishlist is not published yet')

    wishlist.items.sort(key=lambda item: item.position)
    return wishlist


async def ensure_slug_unique(db: AsyncSession, slug: str) -> bool:
    result = await db.execute(select(func.count(Wishlist.id)).where(Wishlist.share_slug == slug))
    return result.scalar_one() == 0


async def get_item_for_update(
    db: AsyncSession,
    wishlist_id: UUID,
    item_id: UUID,
) -> WishlistItem:
    result = await db.execute(
        select(WishlistItem)
        .options(selectinload(WishlistItem.reservation), selectinload(WishlistItem.contributions))
        .where(WishlistItem.id == item_id, WishlistItem.wishlist_id == wishlist_id)
        .with_for_update()
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')
    return item


async def calculate_guest_total_for_item(
    db: AsyncSession,
    item_id: UUID,
    guest_session_id: UUID,
) -> Decimal:
    result = await db.execute(
        select(func.coalesce(func.sum(Contribution.amount), 0)).where(
            Contribution.item_id == item_id,
            Contribution.guest_session_id == guest_session_id,
        )
    )
    value = result.scalar_one()
    return _to_decimal(value)


async def get_active_reservation(db: AsyncSession, item_id: UUID) -> Reservation | None:
    result = await db.execute(select(Reservation).where(Reservation.item_id == item_id))
    reservation = result.scalar_one_or_none()
    if reservation and reservation.is_active:
        return reservation
    return None
