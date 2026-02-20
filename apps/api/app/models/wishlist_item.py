import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ItemMode, ItemStatus
from app.models.mixins import TimestampMixin


class WishlistItem(TimestampMixin, Base):
    __tablename__ = 'wishlist_items'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('wishlists.id', ondelete='CASCADE'), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    mode: Mapped[ItemMode] = mapped_column(
        Enum(ItemMode, name='item_mode'), default=ItemMode.SINGLE, nullable=False
    )
    target_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    collected_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal('0'), nullable=False)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus, name='item_status'), default=ItemStatus.ACTIVE, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    wishlist = relationship('Wishlist', back_populates='items')
    reservation = relationship('Reservation', back_populates='item', uselist=False, cascade='all, delete-orphan')
    contributions = relationship('Contribution', back_populates='item', cascade='all, delete-orphan')
