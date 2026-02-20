from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=False)

    app_env: Literal['local', 'test', 'staging', 'production'] = 'local'
    project_name: str = 'Social Wishlist API'
    api_prefix: str = '/api/v1'

    database_url: str = 'postgresql+asyncpg://postgres:postgres@localhost:5432/wishlist'

    secret_key: str = Field(default='change-me-in-production', min_length=16)
    session_secret: str = Field(default='change-me-session-secret', min_length=16)
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    frontend_url: str = 'http://localhost:3000'
    cors_origins: str = 'http://localhost:3000'

    cookie_secure: bool = False
    cookie_domain: str | None = None

    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None

    link_preview_cache_hours: int = 24
    guest_token_ttl_days: int = 365

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
