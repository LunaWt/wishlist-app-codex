import enum


class WishlistStatus(str, enum.Enum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'


class ItemMode(str, enum.Enum):
    SINGLE = 'single'
    GROUP = 'group'


class ItemStatus(str, enum.Enum):
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    UNAVAILABLE = 'unavailable'


class EventType(str, enum.Enum):
    ITEM_RESERVED = 'item_reserved'
    ITEM_UNRESERVED = 'item_unreserved'
    CONTRIBUTION_ADDED = 'contribution_added'
    ITEM_UPDATED = 'item_updated'
    ITEM_ARCHIVED = 'item_archived'
    WISHLIST_PUBLISHED = 'wishlist_published'
    WISHLIST_CLOSED = 'wishlist_closed'
