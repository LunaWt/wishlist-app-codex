from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ACCESS_COOKIE_NAME, GUEST_HEADER_NAME
from app.core.security import TokenPayloadError, decode_token
from app.db.session import get_db
from app.models.guest_session import GuestSession
from app.models.user import User


async def get_optional_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    access_token: Annotated[str | None, Cookie(alias=ACCESS_COOKIE_NAME)] = None,
) -> User | None:
    if not access_token:
        return None

    try:
        payload = decode_token(access_token, expected_type='access')
    except TokenPayloadError:
        return None

    user_id = payload.get('sub')
    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        return None

    result = await db.execute(select(User).where(User.id == user_uuid, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')
    return user


async def get_refresh_token(
    refresh_token: Annotated[str | None, Cookie(alias='wishlist_refresh_token')] = None,
) -> str:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Refresh token not found')
    return refresh_token


async def get_guest_token(
    guest_token: Annotated[str | None, Header(alias=GUEST_HEADER_NAME)] = None,
) -> str | None:
    return guest_token


async def get_guest_session_from_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    guest_token: Annotated[str | None, Depends(get_guest_token)],
) -> GuestSession | None:
    if not guest_token:
        return None

    try:
        payload = decode_token(guest_token, expected_type='guest')
    except TokenPayloadError:
        return None

    guest_session_id = payload.get('sub')
    try:
        session_uuid = UUID(guest_session_id)
    except (ValueError, TypeError):
        return None

    result = await db.execute(
        select(GuestSession).where(GuestSession.id == session_uuid, GuestSession.is_active.is_(True))
    )
    return result.scalar_one_or_none()


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
OptionalGuestSession = Annotated[GuestSession | None, Depends(get_guest_session_from_token)]
