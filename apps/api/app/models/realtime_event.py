import uuid

from sqlalchemy import Enum, ForeignKey, Integer, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventType
from app.models.mixins import TimestampMixin


class RealtimeEvent(TimestampMixin, Base):
    __tablename__ = 'realtime_events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('wishlists.id', ondelete='CASCADE'), nullable=False, index=True
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name='event_type'), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    wishlist = relationship('Wishlist', back_populates='events')
