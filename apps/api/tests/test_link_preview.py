from __future__ import annotations

from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import create_app


class MockResponse:
    def __init__(self, *, status_code: int = 200, text: str = '', json_data: dict[str, Any] | None = None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request('GET', 'https://example.com')
            response = httpx.Response(status_code=self.status_code, request=request)
            raise httpx.HTTPStatusError('Request failed', request=request, response=response)

    def json(self) -> dict[str, Any]:
        if self._json_data is None:
            raise ValueError('JSON payload is not available')
        return self._json_data


@pytest.fixture
async def app():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app = create_app()
    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield fastapi_app

    await engine.dispose()


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_preview_wildberries_returns_marketplace_data(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import link_preview_service

    monkeypatch.setattr(link_preview_service, '_validate_target_url', lambda _: None)

    async def fake_get(self, url: str, *args, **kwargs):
        if 'card.wb.ru' in url:
            return MockResponse(
                json_data={
                    'data': {
                        'products': [
                            {
                                'name': 'Наушники WB',
                                'salePriceU': 259900,
                                'image': 'https://images.example/wb.jpg',
                            }
                        ]
                    }
                }
            )
        return MockResponse(status_code=404)

    monkeypatch.setattr(httpx.AsyncClient, 'get', fake_get)

    response = await client.post(
        '/api/v1/items/preview',
        json={'url': 'https://www.wildberries.ru/catalog/123456/detail.aspx'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['title'] == 'Наушники WB'
    assert payload['price'] == '2599.00'
    assert payload['image_url'] == 'https://images.example/wb.jpg'
    assert payload['currency'] == 'RUB'
    assert payload['from_cache'] is False


@pytest.mark.asyncio
async def test_preview_ozon_returns_partial_data(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import link_preview_service

    monkeypatch.setattr(link_preview_service, '_validate_target_url', lambda _: None)

    async def fake_get(self, url: str, *args, **kwargs):
        if 'ozon.ru' in url:
            return MockResponse(
                text=(
                    '<html><head>'
                    '<meta property="og:title" content="Смарт-часы Ozon" />'
                    '<meta property="og:image" content="https://images.example/ozon.webp" />'
                    '<meta property="product:price:amount" content="14990" />'
                    '</head></html>'
                )
            )
        return MockResponse(status_code=404)

    monkeypatch.setattr(httpx.AsyncClient, 'get', fake_get)

    response = await client.post(
        '/api/v1/items/preview',
        json={'url': 'https://www.ozon.ru/product/smart-watch-123456789/'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['title'] == 'Смарт-часы Ozon'
    assert payload['price'] == '14990.00'
    assert payload['image_url'] == 'https://images.example/ozon.webp'


@pytest.mark.asyncio
async def test_preview_returns_400_when_remote_is_unavailable(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import link_preview_service

    monkeypatch.setattr(link_preview_service, '_validate_target_url', lambda _: None)

    async def fake_get(self, url: str, *args, **kwargs):
        raise httpx.ConnectError('network down', request=httpx.Request('GET', url))

    monkeypatch.setattr(httpx.AsyncClient, 'get', fake_get)

    response = await client.post(
        '/api/v1/items/preview',
        json={'url': 'https://shop.example/product/1'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'Failed to fetch metadata from URL'
