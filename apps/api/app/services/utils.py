import random
import re
import string


def slugify_title(title: str) -> str:
    normalized = re.sub(r'[^a-zA-Z0-9]+', '-', title).strip('-').lower()
    return normalized[:60] if normalized else 'wishlist'


def generate_slug(title: str) -> str:
    base = slugify_title(title)
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'{base}-{suffix}'
