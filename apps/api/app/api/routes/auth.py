from typing import Annotated

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, DbSession, get_refresh_token
from app.core.config import get_settings
from app.core.security import TokenPayloadError, decode_token
from app.schemas.auth import AuthResponse, LoginRequest, MessageResponse, RegisterRequest
from app.services.auth_service import (
    authenticate_user,
    clear_auth_cookies,
    register_user,
    set_auth_cookies,
    upsert_google_user,
)

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, response: Response, db: DbSession) -> AuthResponse:
    user = await register_user(
        db=db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    set_auth_cookies(response, str(user.id))
    return AuthResponse(user=user)


@router.post('/login', response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    user = await authenticate_user(db=db, email=payload.email, password=payload.password)
    set_auth_cookies(response, str(user.id))
    return AuthResponse(user=user)


@router.post('/logout', response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    clear_auth_cookies(response)
    return MessageResponse(message='Logged out successfully')


@router.get('/me', response_model=AuthResponse)
async def me(user: CurrentUser) -> AuthResponse:
    return AuthResponse(user=user)


@router.post('/refresh', response_model=MessageResponse)
async def refresh_token(
    response: Response,
    refresh_token: Annotated[str, Depends(get_refresh_token)],
) -> MessageResponse:
    try:
        payload = decode_token(refresh_token, expected_type='refresh')
    except TokenPayloadError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token') from exc

    user_id = payload.get('sub')
    set_auth_cookies(response, str(user_id))
    return MessageResponse(message='Token refreshed')


@router.get('/google/start')
async def google_start(request: Request):
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret or not settings.google_redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Google OAuth is not configured',
        )

    oauth = request.app.state.oauth
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get('/google/callback')
async def google_callback(request: Request, db: DbSession):
    settings = get_settings()
    oauth = request.app.state.oauth

    success_url = f"{settings.frontend_url}/auth/callback?status=success"
    failure_url = f"{settings.frontend_url}/auth/callback?status=error"

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url=failure_url)

    user_info = token.get('userinfo')
    if not user_info:
        try:
            user_info = await oauth.google.parse_id_token(request, token)
        except Exception:
            return RedirectResponse(url=failure_url)

    if not user_info:
        return RedirectResponse(url=failure_url)

    email = user_info.get('email')
    sub = user_info.get('sub')
    display_name = user_info.get('name') or (email.split('@')[0] if email else 'Google User')

    if not email or not sub:
        return RedirectResponse(url=failure_url)

    user = await upsert_google_user(
        db=db,
        email=email,
        display_name=display_name,
        provider_account_id=sub,
    )

    response = RedirectResponse(url=success_url)
    set_auth_cookies(response, str(user.id))
    return response
