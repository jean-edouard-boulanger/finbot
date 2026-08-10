"""add portfolio tables

Revision ID: a2d5c9e13f74
Revises: f1c8a3d27b50
Create Date: 2026-08-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from finbot.core.db.types import JSONEncoded


# revision identifiers, used by Alembic.
revision = 'a2d5c9e13f74'
down_revision = 'f1c8a3d27b50'
branch_labels = None
depends_on = None


# `subaccountitemtype` already exists in the database (it backs the snapshot / history item tables),
# so it must be reused rather than re-created here.
SUB_ACCOUNT_ITEM_TYPE = postgresql.ENUM('Asset', 'Liability', name='subaccountitemtype', create_type=False)
PRICE_SOURCE = sa.Enum('Manual', 'Proxy', name='portfolioentrypricesource')


def upgrade():
    op.create_table(
        'finbot_portfolios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_account_id', sa.Integer(), sa.ForeignKey('finbot_user_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('linked_account_id', sa.Integer(), sa.ForeignKey('finbot_linked_accounts.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_portfolios_user_account', 'finbot_portfolios', ['user_account_id'])

    op.create_table(
        'finbot_portfolio_sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('portfolio_id', sa.Integer(), sa.ForeignKey('finbot_portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.String(64), nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('account_type', sa.String(32), nullable=False),
        sa.Column('account_sub_type', sa.String(32)),
        sa.Column('custom_columns', JSONEncoded(), nullable=False, server_default='[]'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('portfolio_id', 'section_id', name='uidx_portfolio_sections_portfolio_section_id'),
    )

    op.create_table(
        'finbot_portfolio_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('portfolio_section_id', sa.Integer(), sa.ForeignKey('finbot_portfolio_sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('item_type', SUB_ACCOUNT_ITEM_TYPE, nullable=False),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('asset_class', sa.String(32)),
        sa.Column('asset_type', sa.String(32)),
        sa.Column('liability_type', sa.String(32)),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('units', sa.Numeric(), nullable=False, server_default='1'),
        sa.Column('price_source', PRICE_SOURCE, nullable=False),
        sa.Column('manual_unit_price', sa.Numeric()),
        sa.Column('manual_price_updated_at', sa.DateTime(timezone=True)),
        sa.Column('proxy_symbol', sa.String(32)),
        sa.Column('last_resolved_unit_price', sa.Numeric()),
        sa.Column('last_resolved_price_at', sa.DateTime(timezone=True)),
        sa.Column('isin_code', sa.String(16)),
        sa.Column('custom_values', JSONEncoded()),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_portfolio_entries_section', 'finbot_portfolio_entries', ['portfolio_section_id'])


def downgrade():
    op.drop_index('idx_portfolio_entries_section', table_name='finbot_portfolio_entries')
    op.drop_table('finbot_portfolio_entries')
    op.drop_table('finbot_portfolio_sections')
    op.drop_index('idx_portfolios_user_account', table_name='finbot_portfolios')
    op.drop_table('finbot_portfolios')
    PRICE_SOURCE.drop(op.get_bind(), checkfirst=True)
