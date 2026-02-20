import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Reservation(TimestampMixin, Base):
    __tablename__ = 'reservations'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('wishlist_items.id', ondelete='CASCADE'), nullable=False, unique=True
    )
    guest_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('guest_sessions.id', ondelete='CASCADE'), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    item = relationship('WishlistItem', back_populates='reservation')
    guest_session = relationship('GuestSession', back_populates='reservations')
