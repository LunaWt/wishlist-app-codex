from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.enums import EventType, ItemMode, ItemStatus, WishlistStatus
from app.models.wishlist import Wishlist
from app.models.wishlist_item import WishlistItem
from app.schemas.auth import MessageResponse
from app.schemas.wishlist import (
    OwnerWishlistDetail,
    WishlistCreateRequest,
    WishlistItemCreateRequest,
    WishlistItemReorderRequest,
    WishlistItemUpdateRequest,
    WishlistSummary,
    WishlistUpdateRequest,
)
from app.services.event_service import publish_event
from app.services.utils import generate_slug
from app.services.wishlist_service import (
    build_owner_item_view,
    ensure_slug_unique,
    get_owner_wishlist_or_404,
)

router = APIRouter(prefix='/wishlists', tags=['wishlists'])


def _owner_detail_response(wishlist: Wishlist) -> OwnerWishlistDetail:
    return OwnerWishlistDetail(
        id=wishlist.id,
        title=wishlist.title,
        description=wishlist.description,
        currency=wishlist.currency,
        status=wishlist.status,
        share_slug=wishlist.share_slug,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        items=[build_owner_item_view(item) for item in sorted(wishlist.items, key=lambda i: i.position)],
    )


@router.post('', response_model=OwnerWishlistDetail, status_code=status.HTTP_201_CREATED)
async def create_wishlist(payload: WishlistCreateRequest, db: DbSession, user: CurrentUser) -> OwnerWishlistDetail:
    wishlist = Wishlist(
        owner_id=user.id,
        title=payload.title,
        description=payload.description,
        currency=payload.currency,
        status=WishlistStatus.DRAFT,
    )
    db.add(wishlist)
    await db.commit()
    await db.refresh(wishlist)
    await db.refresh(wishlist, attribute_names=['items'])
    return _owner_detail_response(wishlist)


@router.get('/mine', response_model=list[WishlistSummary])
async def list_my_wishlists(db: DbSession, user: CurrentUser) -> list[WishlistSummary]:
    result = await db.execute(
        select(Wishlist).where(Wishlist.owner_id == user.id).order_by(Wishlist.created_at.desc())
    )
    wishlists = result.scalars().all()
    return [
        WishlistSummary(
            id=wishlist.id,
            title=wishlist.title,
            description=wishlist.description,
            currency=wishlist.currency,
            status=wishlist.status,
            share_slug=wishlist.share_slug,
            created_at=wishlist.created_at,
            updated_at=wishlist.updated_at,
        )
        for wishlist in wishlists
    ]


@router.get('/{wishlist_id}', response_model=OwnerWishlistDetail)
async def get_wishlist(wishlist_id: UUID, db: DbSession, user: CurrentUser) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.patch('/{wishlist_id}', response_model=OwnerWishlistDetail)
async def update_wishlist(
    wishlist_id: UUID,
    payload: WishlistUpdateRequest,
    db: DbSession,
    user: CurrentUser,
) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(wishlist, field, value)

    wishlist.updated_at = datetime.now(UTC)
    await db.commit()
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.post('/{wishlist_id}/publish', response_model=OwnerWishlistDetail)
async def publish_wishlist(wishlist_id: UUID, db: DbSession, user: CurrentUser) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)

    if not wishlist.share_slug:
        for _ in range(15):
            candidate = generate_slug(wishlist.title)
            if await ensure_slug_unique(db, candidate):
                wishlist.share_slug = candidate
                break
        if not wishlist.share_slug:
            raise HTTPException(status_code=500, detail='Failed to generate a public slug')

    wishlist.status = WishlistStatus.PUBLISHED
    wishlist.closed_at = None

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.WISHLIST_PUBLISHED,
        payload={'wishlist_id': str(wishlist.id)},
    )
    await db.commit()

    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.post('/{wishlist_id}/close', response_model=OwnerWishlistDetail)
async def close_wishlist(wishlist_id: UUID, db: DbSession, user: CurrentUser) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    wishlist.status = WishlistStatus.CLOSED
    wishlist.closed_at = datetime.now(UTC)

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.WISHLIST_CLOSED,
        payload={'wishlist_id': str(wishlist.id)},
    )
    await db.commit()

    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.post('/{wishlist_id}/items', response_model=OwnerWishlistDetail, status_code=status.HTTP_201_CREATED)
async def create_item(
    wishlist_id: UUID,
    payload: WishlistItemCreateRequest,
    db: DbSession,
    user: CurrentUser,
) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)

    if wishlist.status == WishlistStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Closed wishlist cannot be edited')

    if payload.mode == ItemMode.GROUP and not payload.target_amount and not payload.price:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Group item requires target_amount or price',
        )

    max_position = max([item.position for item in wishlist.items], default=-1)
    position = payload.position if payload.position is not None else max_position + 1

    item = WishlistItem(
        wishlist_id=wishlist.id,
        title=payload.title,
        product_url=str(payload.product_url) if payload.product_url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        notes=payload.notes,
        price=payload.price,
        mode=payload.mode,
        target_amount=payload.target_amount or (payload.price if payload.mode == ItemMode.GROUP else None),
        collected_amount=Decimal('0'),
        position=position,
    )
    db.add(item)

    await db.flush()
    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_UPDATED,
        item_id=item.id,
        payload={
            'item_id': str(item.id),
            'action': 'created',
            'title': item.title,
        },
    )

    await db.commit()
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.patch('/{wishlist_id}/items/{item_id}', response_model=OwnerWishlistDetail)
async def update_item(
    wishlist_id: UUID,
    item_id: UUID,
    payload: WishlistItemUpdateRequest,
    db: DbSession,
    user: CurrentUser,
) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    item = next((item for item in wishlist.items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')

    updates = payload.model_dump(exclude_unset=True)
    if 'product_url' in updates and updates['product_url'] is not None:
        updates['product_url'] = str(updates['product_url'])
    if 'image_url' in updates and updates['image_url'] is not None:
        updates['image_url'] = str(updates['image_url'])

    for field, value in updates.items():
        setattr(item, field, value)

    if item.mode == ItemMode.GROUP and not item.target_amount and item.price:
        item.target_amount = item.price

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_UPDATED,
        item_id=item.id,
        payload={
            'item_id': str(item.id),
            'action': 'updated',
        },
    )

    await db.commit()
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.post('/{wishlist_id}/items/{item_id}/archive', response_model=OwnerWishlistDetail)
async def archive_item(wishlist_id: UUID, item_id: UUID, db: DbSession, user: CurrentUser) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    item = next((item for item in wishlist.items if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Item not found')

    item.status = ItemStatus.ARCHIVED

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_ARCHIVED,
        item_id=item.id,
        payload={
            'item_id': str(item.id),
            'action': 'archived',
        },
    )

    await db.commit()
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.post('/{wishlist_id}/items/reorder', response_model=OwnerWishlistDetail)
async def reorder_items(
    wishlist_id: UUID,
    payload: WishlistItemReorderRequest,
    db: DbSession,
    user: CurrentUser,
) -> OwnerWishlistDetail:
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)

    existing_ids = {item.id for item in wishlist.items}
    incoming_ids = payload.item_ids

    if set(incoming_ids) != existing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='item_ids must include all current items exactly once',
        )

    position_map = {item_id: index for index, item_id in enumerate(incoming_ids)}
    for item in wishlist.items:
        item.position = position_map[item.id]

    await publish_event(
        db,
        wishlist_id=wishlist.id,
        share_slug=wishlist.share_slug,
        event_type=EventType.ITEM_UPDATED,
        payload={
            'action': 'reordered',
            'item_ids': [str(item_id) for item_id in incoming_ids],
        },
    )

    await db.commit()
    wishlist = await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return _owner_detail_response(wishlist)


@router.get('/{wishlist_id}/stats', response_model=MessageResponse)
async def stats_placeholder(wishlist_id: UUID, db: DbSession, user: CurrentUser) -> MessageResponse:
    await get_owner_wishlist_or_404(db=db, wishlist_id=wishlist_id, owner_id=user.id)
    return MessageResponse(message='Aggregated stats are included in wishlist details')
