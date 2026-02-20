import uuid

from sqlalchemy import ForeignKey, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class OAuthAccount(TimestampMixin, Base):
    __tablename__ = 'oauth_accounts'
    __table_args__ = (
        UniqueConstraint('provider', 'provider_account_id', name='uq_oauth_provider_account'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship('User', back_populates='oauth_accounts')
