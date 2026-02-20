import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class GuestSession(TimestampMixin, Base):
    __tablename__ = 'guest_sessions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('wishlists.id', ondelete='CASCADE'), nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    wishlist = relationship('Wishlist', back_populates='guest_sessions')
    reservations = relationship('Reservation', back_populates='guest_session')
    contributions = relationship('Contribution', back_populates='guest_session')
