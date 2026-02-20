import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import create_app


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
async def test_auth_and_wishlist_flow(client: AsyncClient, app) -> None:
    register_payload = {
        'email': 'owner@example.com',
        'password': 'password123',
        'display_name': 'Owner Name',
    }
    register_response = await client.post('/api/v1/auth/register', json=register_payload)
    assert register_response.status_code == 201

    create_wishlist_response = await client.post(
        '/api/v1/wishlists',
        json={
            'title': 'Birthday 2026',
            'description': 'Gift list',
            'currency': 'RUB',
        },
    )
    assert create_wishlist_response.status_code == 201
    wishlist_id = create_wishlist_response.json()['id']

    single_item_response = await client.post(
        f'/api/v1/wishlists/{wishlist_id}/items',
        json={
            'title': 'Book',
            'mode': 'single',
            'price': '1500.00',
        },
    )
    assert single_item_response.status_code == 201

    group_item_response = await client.post(
        f'/api/v1/wishlists/{wishlist_id}/items',
        json={
            'title': 'Headphones',
            'mode': 'group',
            'target_amount': '10000.00',
        },
    )
    assert group_item_response.status_code == 201

    publish_response = await client.post(f'/api/v1/wishlists/{wishlist_id}/publish')
    assert publish_response.status_code == 200
    share_slug = publish_response.json()['share_slug']

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as guest_client:
        public_response = await guest_client.get(f'/api/v1/public/w/{share_slug}')
        assert public_response.status_code == 200
        assert public_response.json()['viewer_kind'] == 'anonymous'

        guest_session_response = await guest_client.post(
            f'/api/v1/public/w/{share_slug}/guest-session',
            json={'name': 'Friend'},
        )
        assert guest_session_response.status_code == 200
        guest_token = guest_session_response.json()['token']

        items = public_response.json()['items']
        single_item_id = next(item['id'] for item in items if item['mode'] == 'single')
        group_item_id = next(item['id'] for item in items if item['mode'] == 'group')

        reserve_response = await guest_client.post(
            f'/api/v1/public/w/{share_slug}/items/{single_item_id}/reserve',
            headers={'X-Guest-Token': guest_token},
        )
        assert reserve_response.status_code == 200

        contribution_response = await guest_client.post(
            f'/api/v1/public/w/{share_slug}/items/{group_item_id}/contributions',
            headers={'X-Guest-Token': guest_token},
            json={'amount': '2500.00'},
        )
        assert contribution_response.status_code == 200
        assert contribution_response.json()['accepted_amount'] == '2500.00'

        public_guest_view = await guest_client.get(
            f'/api/v1/public/w/{share_slug}',
            headers={'X-Guest-Token': guest_token},
        )
        assert public_guest_view.status_code == 200
        assert public_guest_view.json()['viewer_kind'] == 'guest'

    owner_view = await client.get(f'/api/v1/wishlists/{wishlist_id}')
    assert owner_view.status_code == 200
    owner_items = owner_view.json()['items']
    assert any(item['is_reserved'] for item in owner_items)
    assert all('reserved_by_you' not in item for item in owner_items)
