from datetime import UTC, datetime

from fastapi import HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User


def set_auth_cookies(response: Response, user_id: str) -> None:
    settings = get_settings()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    common = {
        'httponly': True,
        'secure': settings.cookie_secure,
        'samesite': 'lax',
        'domain': settings.cookie_domain,
        'path': '/',
    }
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **common,
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        **common,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    common = {
        'httponly': True,
        'secure': settings.cookie_secure,
        'samesite': 'lax',
        'domain': settings.cookie_domain,
        'path': '/',
    }
    response.delete_cookie(ACCESS_COOKIE_NAME, **common)
    response.delete_cookie(REFRESH_COOKIE_NAME, **common)


async def register_user(db: AsyncSession, email: str, password: str, display_name: str) -> User:
    existing_result = await db.execute(select(User).where(User.email == email.lower()))
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='User with this email already exists',
        )

    user = User(
        email=email.lower(),
        password_hash=get_password_hash(password),
        display_name=display_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email.lower(), User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')
    return user


async def upsert_google_user(
    db: AsyncSession,
    email: str,
    display_name: str,
    provider_account_id: str,
) -> User:
    from app.models.oauth_account import OAuthAccount

    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=email.lower(), display_name=display_name, password_hash=None)
        db.add(user)
        await db.flush()

    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == 'google',
            OAuthAccount.provider_account_id == provider_account_id,
        )
    )
    oauth = oauth_result.scalar_one_or_none()
    if not oauth:
        oauth = OAuthAccount(
            user_id=user.id,
            provider='google',
            provider_account_id=provider_account_id,
            email=email.lower(),
        )
        db.add(oauth)

    user.display_name = display_name
    user.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(user)
    return user
