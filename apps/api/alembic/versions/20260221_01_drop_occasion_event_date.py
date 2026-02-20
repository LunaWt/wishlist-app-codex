"""drop wishlist occasion and event_date

Revision ID: 20260221_01
Revises: 20260220_01
Create Date: 2026-02-21
"""

from alembic import op
import sqlalchemy as sa


revision = '20260221_01'
down_revision = '20260220_01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('wishlists', 'occasion')
    op.drop_column('wishlists', 'event_date')


def downgrade() -> None:
    op.add_column('wishlists', sa.Column('event_date', sa.Date(), nullable=True))
    op.add_column('wishlists', sa.Column('occasion', sa.String(length=120), nullable=True))
