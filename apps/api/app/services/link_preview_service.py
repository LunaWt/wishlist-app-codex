from __future__ import annotations

import ipaddress
import json
import re
import socket
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.link_preview import LinkPreview

PRICE_REGEX = re.compile(r'([0-9][0-9\s]*(?:[.,][0-9]{1,2})?)')
WB_NM_ID_PATTERNS = [
    re.compile(r'/catalog/(?P<nm_id>\d+)'),
    re.compile(r'/product/(?P<nm_id>\d+)'),
    re.compile(r'-(?P<nm_id>\d{6,})/?$'),
]
WB_DETAIL_ENDPOINTS = [
    'https://card.wb.ru/cards/v4/detail',
    'https://card.wb.ru/cards/v2/detail',
    'https://card.wb.ru/cards/detail',
]
OZON_DOMAINS = {'ozon.ru', 'www.ozon.ru'}
WB_DOMAINS = {'wildberries.ru', 'www.wildberries.ru', 'wb.ru', 'www.wb.ru'}

OZON_TITLE_REGEX = re.compile(r'"title"\s*:\s*"([^"]{3,255})"')
OZON_PRICE_REGEX = re.compile(
    r'"(?:finalPrice|price|cardPrice|marketingPrice|priceValue)"\s*:\s*"?([0-9][0-9\s,.]*)"?'
)
OZON_IMAGE_REGEX = re.compile(r'https:\\/\\/[^"\\]+(?:jpg|jpeg|png|webp)')



def _normalize_hostname(hostname: str | None) -> str:
    return (hostname or '').strip().lower()



def _is_private_ip(ip: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return any(
        [
            ip_obj.is_private,
            ip_obj.is_loopback,
            ip_obj.is_link_local,
            ip_obj.is_reserved,
            ip_obj.is_multicast,
            ip_obj.is_unspecified,
        ]
    )



def _validate_target_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Only HTTP/HTTPS URLs are allowed')
    if not parsed.hostname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid URL')

    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to resolve host') from exc

    for info in infos:
        ip = info[4][0]
        if _is_private_ip(ip):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Requests to private hosts are blocked')



def _extract_price(meta_content: str | None) -> Decimal | None:
    if not meta_content:
        return None
    matched = PRICE_REGEX.search(meta_content)
    if not matched:
        return None

    value = matched.group(1).replace(' ', '').replace(',', '.')
    try:
        return Decimal(value).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return None



def _parse_price_value(value: Any, *, divide_by_hundred: bool = False) -> Decimal | None:
    if value is None:
        return None

    if isinstance(value, (int, float, Decimal)):
        parsed = Decimal(str(value))
    elif isinstance(value, str):
        normalized = value.strip().replace(' ', '').replace(',', '.')
        if not normalized:
            return None
        try:
            parsed = Decimal(normalized)
        except InvalidOperation:
            return _extract_price(value)
    else:
        return None

    if divide_by_hundred:
        parsed = parsed / Decimal('100')

    try:
        return parsed.quantize(Decimal('0.01'))
    except InvalidOperation:
        return None



def _extract_from_jsonld(soup: BeautifulSoup) -> tuple[str | None, str | None, Decimal | None, str | None]:
    for script in soup.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            payload = json.loads(script.text)
        except json.JSONDecodeError:
            continue

        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            title = entry.get('name')
            image = entry.get('image')
            if isinstance(image, list):
                image = image[0] if image else None

            offers = entry.get('offers')
            price = None
            currency = None
            if isinstance(offers, dict):
                price = _extract_price(str(offers.get('price')))
                currency = offers.get('priceCurrency')

            if title or image or price or currency:
                return title, image, price, currency

    return None, None, None, None



def _extract_metadata(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, 'html.parser')

    def get_meta(*keys: str) -> str | None:
        for key in keys:
            node = soup.find('meta', attrs={'property': key}) or soup.find('meta', attrs={'name': key})
            if node and node.get('content'):
                return str(node['content']).strip()
        return None

    title = get_meta('og:title', 'twitter:title')
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()

    image = get_meta('og:image', 'twitter:image')
    price_raw = get_meta('product:price:amount', 'og:price:amount', 'price')
    currency = get_meta('product:price:currency', 'og:price:currency')
    price = _extract_price(price_raw)

    if not any([title, image, price, currency]):
        jsonld_title, jsonld_image, jsonld_price, jsonld_currency = _extract_from_jsonld(soup)
        title = title or jsonld_title
        image = image or jsonld_image
        price = price or jsonld_price
        currency = currency or jsonld_currency

    return {
        'title': title,
        'image_url': image,
        'price': price,
        'currency': currency.upper() if currency else None,
    }



def _extract_wildberries_nm_id(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    nm_from_query = query.get('nm')
    if nm_from_query and nm_from_query[0].isdigit():
        return nm_from_query[0]

    full_path = f'{parsed.path}?{parsed.query}'
    for pattern in WB_NM_ID_PATTERNS:
        match = pattern.search(full_path)
        if match:
            return match.group('nm_id')

    return None



def _extract_wb_product(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    products = payload.get('products')
    if not isinstance(products, list):
        data = payload.get('data')
        if isinstance(data, dict):
            products = data.get('products')

    if isinstance(products, list) and products:
        first = products[0]
        if isinstance(first, dict):
            return first

    return None



def _extract_wb_image(product: dict[str, Any]) -> str | None:
    image_candidates = [
        product.get('image'),
        product.get('thumb'),
        product.get('cover'),
        product.get('photo'),
    ]

    media = product.get('media')
    if isinstance(media, dict):
        image_candidates.extend([media.get('photo'), media.get('preview')])

    images = product.get('images')
    if isinstance(images, list) and images:
        image_candidates.append(images[0])

    for candidate in image_candidates:
        if isinstance(candidate, str) and candidate.strip():
            value = candidate.strip().replace('\\/', '/')
            if value.startswith('//'):
                return f'https:{value}'
            return value

    return None



def _extract_wb_price(product: dict[str, Any]) -> Decimal | None:
    cents_fields = ['salePriceU', 'priceU', 'clientPriceU', 'extendedPriceU']
    for field in cents_fields:
        price = _parse_price_value(product.get(field), divide_by_hundred=True)
        if price and price > 0:
            return price

    regular_fields = ['salePrice', 'price', 'clientPrice', 'extendedPrice']
    for field in regular_fields:
        price = _parse_price_value(product.get(field), divide_by_hundred=False)
        if price and price > 0:
            return price

    return None



async def _fetch_wildberries_metadata(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    nm_id = _extract_wildberries_nm_id(url)
    if not nm_id:
        return {}

    params = {
        'appType': '1',
        'curr': 'rub',
        'dest': '-1257786',
        'spp': '30',
        'nm': nm_id,
    }

    for endpoint in WB_DETAIL_ENDPOINTS:
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            continue

        product = _extract_wb_product(payload)
        if not product:
            continue

        title = str(product.get('name') or product.get('imt_name') or '').strip() or None
        image = _extract_wb_image(product)
        price = _extract_wb_price(product)

        if title or image or price:
            return {
                'title': title,
                'image_url': image,
                'price': price,
                'currency': 'RUB',
            }

    return {}



def _decode_json_escaped(value: str) -> str:
    raw = value.strip()
    if not raw:
        return raw

    try:
        return json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        return raw



def _extract_ozon_script_metadata(html: str) -> dict[str, Any]:
    title: str | None = None
    image_url: str | None = None
    price: Decimal | None = None

    title_match = OZON_TITLE_REGEX.search(html)
    if title_match:
        title = _decode_json_escaped(title_match.group(1))

    image_match = OZON_IMAGE_REGEX.search(html)
    if image_match:
        image_url = image_match.group(0).replace('\\/', '/')

    price_match = OZON_PRICE_REGEX.search(html)
    if price_match:
        price = _extract_price(price_match.group(1))

    return {
        'title': title,
        'image_url': image_url,
        'price': price,
        'currency': 'RUB' if price else None,
    }



async def _fetch_ozon_metadata(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        return {}

    metadata = _extract_metadata(response.text)
    script_metadata = _extract_ozon_script_metadata(response.text)

    title = metadata.get('title') or script_metadata.get('title')
    image_url = metadata.get('image_url') or script_metadata.get('image_url')
    price = metadata.get('price') or script_metadata.get('price')
    currency = metadata.get('currency') or script_metadata.get('currency')

    if currency:
        currency = currency.upper()

    if title or image_url or price:
        return {
            'title': title,
            'image_url': image_url,
            'price': price,
            'currency': currency,
        }

    return {}



async def _fetch_generic_metadata(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Failed to fetch metadata from URL',
        ) from exc

    return _extract_metadata(response.text)



async def get_or_fetch_link_preview(db: AsyncSession, url: str) -> dict[str, Any]:
    settings = get_settings()

    result = await db.execute(select(LinkPreview).where(LinkPreview.url == url))
    cached = result.scalar_one_or_none()
    now = datetime.now(UTC)

    if cached and now - cached.updated_at < timedelta(hours=settings.link_preview_cache_hours):
        return {
            'title': cached.title,
            'image_url': cached.image_url,
            'price': cached.price,
            'currency': cached.currency,
            'source_url': cached.url,
            'from_cache': True,
        }

    _validate_target_url(url)

    hostname = _normalize_hostname(urlparse(url).hostname)
    timeout = httpx.Timeout(7.0, connect=3.0)
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        metadata: dict[str, Any] = {}

        if hostname in WB_DOMAINS:
            metadata = await _fetch_wildberries_metadata(client, url)
        elif hostname in OZON_DOMAINS:
            metadata = await _fetch_ozon_metadata(client, url)

        if not any(metadata.get(field) for field in ('title', 'image_url', 'price')):
            metadata = await _fetch_generic_metadata(client, url)

    if metadata.get('currency'):
        metadata['currency'] = str(metadata['currency']).upper()

    if not cached:
        cached = LinkPreview(url=url)
        db.add(cached)

    cached.title = metadata.get('title')
    cached.image_url = metadata.get('image_url')
    cached.price = metadata.get('price')
    cached.currency = metadata.get('currency')
    cached.raw_data = {
        'source_domain': hostname,
        'preview_fields': {
            'title': bool(cached.title),
            'image_url': bool(cached.image_url),
            'price': bool(cached.price),
        },
    }

    await db.commit()
    await db.refresh(cached)

    return {
        'title': cached.title,
        'image_url': cached.image_url,
        'price': cached.price,
        'currency': cached.currency,
        'source_url': cached.url,
        'from_cache': False,
    }
