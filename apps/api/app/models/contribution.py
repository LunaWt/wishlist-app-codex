import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Contribution(TimestampMixin, Base):
    __tablename__ = 'contributions'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('wishlist_items.id', ondelete='CASCADE'), nullable=False, index=True
    )
    guest_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('guest_sessions.id', ondelete='CASCADE'), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    item = relationship('WishlistItem', back_populates='contributions')
    guest_session = relationship('GuestSession', back_populates='contributions')
