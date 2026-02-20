from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')


class TokenPayloadError(Exception):
    """Raised when token payload is invalid."""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_payload: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        'sub': subject,
        'type': token_type,
        'iat': int(now.timestamp()),
        'exp': int((now + expires_delta).timestamp()),
    }
    if extra_payload:
        payload.update(extra_payload)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(user_id, 'access', timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(user_id, 'refresh', timedelta(days=settings.refresh_token_expire_days))


def create_guest_token(guest_session_id: str, wishlist_id: str, expires_days: int) -> str:
    return _create_token(
        subject=guest_session_id,
        token_type='guest',
        expires_delta=timedelta(days=expires_days),
        extra_payload={'wishlist_id': wishlist_id},
    )


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise TokenPayloadError('Invalid token') from exc

    token_type = payload.get('type')
    if expected_type and token_type != expected_type:
        raise TokenPayloadError('Unexpected token type')

    subject = payload.get('sub')
    if not subject:
        raise TokenPayloadError('Token subject is missing')

    return payload
