import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WishlistStatus
from app.models.mixins import TimestampMixin


class Wishlist(TimestampMixin, Base):
    __tablename__ = 'wishlists'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default='RUB', nullable=False)
    status: Mapped[WishlistStatus] = mapped_column(
        Enum(WishlistStatus, name='wishlist_status'), default=WishlistStatus.DRAFT, nullable=False
    )
    share_slug: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship('User', back_populates='wishlists')
    items = relationship('WishlistItem', back_populates='wishlist', cascade='all, delete-orphan')
    guest_sessions = relationship('GuestSession', back_populates='wishlist', cascade='all, delete-orphan')
    events = relationship('RealtimeEvent', back_populates='wishlist', cascade='all, delete-orphan')
