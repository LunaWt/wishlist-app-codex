from __future__ import annotations

import ipaddress
import json
import re
import socket
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.link_preview import LinkPreview

PRICE_REGEX = re.compile(r'([0-9]+(?:[.,][0-9]{1,2})?)')


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

    value = matched.group(1).replace(',', '.')
    try:
        return Decimal(value).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
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

    title = get_meta('og:title', 'twitter:title') or (soup.title.string.strip() if soup.title and soup.title.string else None)
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

    timeout = httpx.Timeout(6.0, connect=3.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={'User-Agent': 'WishlistBot/1.0'}) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Failed to fetch metadata from URL',
            ) from exc

    metadata = _extract_metadata(response.text)

    if not cached:
        cached = LinkPreview(url=url)
        db.add(cached)

    cached.title = metadata['title']
    cached.image_url = metadata['image_url']
    cached.price = metadata['price']
    cached.currency = metadata['currency']
    cached.raw_data = {'status_code': response.status_code}

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
