"""initial schema

Revision ID: 20260220_01
Revises: 
Create Date: 2026-02-20

"""

from alembic import op
import sqlalchemy as sa


revision = '20260220_01'
down_revision = None
branch_labels = None
depends_on = None


wishlist_status = sa.Enum('draft', 'published', 'closed', name='wishlist_status')
item_mode = sa.Enum('single', 'group', name='item_mode')
item_status = sa.Enum('active', 'archived', 'unavailable', name='item_status')
event_type = sa.Enum(
    'item_reserved',
    'item_unreserved',
    'contribution_added',
    'item_updated',
    'item_archived',
    'wishlist_published',
    'wishlist_closed',
    name='event_type',
)


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_account_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_oauth_accounts_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_oauth_accounts')),
        sa.UniqueConstraint('provider', 'provider_account_id', name='uq_oauth_provider_account'),
    )
    op.create_index(op.f('ix_oauth_accounts_user_id'), 'oauth_accounts', ['user_id'], unique=False)

    op.create_table(
        'wishlists',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=180), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('occasion', sa.String(length=120), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='RUB'),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('status', wishlist_status, nullable=False, server_default='draft'),
        sa.Column('share_slug', sa.String(length=128), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_wishlists_owner_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_wishlists')),
        sa.UniqueConstraint('share_slug', name=op.f('uq_wishlists_share_slug')),
    )
    op.create_index(op.f('ix_wishlists_owner_id'), 'wishlists', ['owner_id'], unique=False)
    op.create_index(op.f('ix_wishlists_share_slug'), 'wishlists', ['share_slug'], unique=False)

    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('wishlist_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('product_url', sa.String(length=2048), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=True),
        sa.Column('mode', item_mode, nullable=False, server_default='single'),
        sa.Column('target_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('collected_amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('status', item_status, nullable=False, server_default='active'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['wishlist_id'], ['wishlists.id'], name=op.f('fk_wishlist_items_wishlist_id_wishlists'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_wishlist_items')),
    )
    op.create_index(op.f('ix_wishlist_items_wishlist_id'), 'wishlist_items', ['wishlist_id'], unique=False)

    op.create_table(
        'guest_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('wishlist_id', sa.Uuid(), nullable=False),
        sa.Column('display_name', sa.String(length=120), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['wishlist_id'], ['wishlists.id'], name=op.f('fk_guest_sessions_wishlist_id_wishlists'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_guest_sessions')),
    )
    op.create_index(op.f('ix_guest_sessions_wishlist_id'), 'guest_sessions', ['wishlist_id'], unique=False)

    op.create_table(
        'reservations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('guest_session_id', sa.Uuid(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('reserved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['guest_session_id'], ['guest_sessions.id'], name=op.f('fk_reservations_guest_session_id_guest_sessions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['wishlist_items.id'], name=op.f('fk_reservations_item_id_wishlist_items'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reservations')),
        sa.UniqueConstraint('item_id', name=op.f('uq_reservations_item_id')),
    )
    op.create_index(op.f('ix_reservations_guest_session_id'), 'reservations', ['guest_session_id'], unique=False)

    op.create_table(
        'contributions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('guest_session_id', sa.Uuid(), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['guest_session_id'], ['guest_sessions.id'], name=op.f('fk_contributions_guest_session_id_guest_sessions'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['wishlist_items.id'], name=op.f('fk_contributions_item_id_wishlist_items'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_contributions')),
    )
    op.create_index(op.f('ix_contributions_item_id'), 'contributions', ['item_id'], unique=False)
    op.create_index(op.f('ix_contributions_guest_session_id'), 'contributions', ['guest_session_id'], unique=False)

    op.create_table(
        'realtime_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('wishlist_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', event_type, nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['wishlist_id'], ['wishlists.id'], name=op.f('fk_realtime_events_wishlist_id_wishlists'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_realtime_events')),
    )
    op.create_index(op.f('ix_realtime_events_wishlist_id'), 'realtime_events', ['wishlist_id'], unique=False)
    op.create_index(op.f('ix_realtime_events_item_id'), 'realtime_events', ['item_id'], unique=False)
    op.create_index(op.f('ix_realtime_events_event_type'), 'realtime_events', ['event_type'], unique=False)

    op.create_table(
        'link_previews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('price', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_link_previews')),
        sa.UniqueConstraint('url', name=op.f('uq_link_previews_url')),
    )


def downgrade() -> None:
    op.drop_table('link_previews')
    op.drop_index(op.f('ix_realtime_events_event_type'), table_name='realtime_events')
    op.drop_index(op.f('ix_realtime_events_item_id'), table_name='realtime_events')
    op.drop_index(op.f('ix_realtime_events_wishlist_id'), table_name='realtime_events')
    op.drop_table('realtime_events')
    op.drop_index(op.f('ix_contributions_guest_session_id'), table_name='contributions')
    op.drop_index(op.f('ix_contributions_item_id'), table_name='contributions')
    op.drop_table('contributions')
    op.drop_index(op.f('ix_reservations_guest_session_id'), table_name='reservations')
    op.drop_table('reservations')
    op.drop_index(op.f('ix_guest_sessions_wishlist_id'), table_name='guest_sessions')
    op.drop_table('guest_sessions')
    op.drop_index(op.f('ix_wishlist_items_wishlist_id'), table_name='wishlist_items')
    op.drop_table('wishlist_items')
    op.drop_index(op.f('ix_wishlists_share_slug'), table_name='wishlists')
    op.drop_index(op.f('ix_wishlists_owner_id'), table_name='wishlists')
    op.drop_table('wishlists')
    op.drop_index(op.f('ix_oauth_accounts_user_id'), table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    event_type.drop(op.get_bind(), checkfirst=True)
    item_status.drop(op.get_bind(), checkfirst=True)
    item_mode.drop(op.get_bind(), checkfirst=True)
    wishlist_status.drop(op.get_bind(), checkfirst=True)
