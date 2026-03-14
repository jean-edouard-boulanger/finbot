"""add merchant tables

Revision ID: c4e8f1a2b3d5
Revises: 85fe4aa82083
Create Date: 2026-03-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = 'c4e8f1a2b3d5'
down_revision = '85fe4aa82083'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'finbot_merchants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('description', sa.String(512)),
        sa.Column('category', sa.String(128)),
        sa.Column('website_url', sa.String(512)),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True)),
    )

    op.create_table(
        'finbot_merchant_description_patterns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('merchant_id', sa.Integer(), sa.ForeignKey('finbot_merchants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sanitized_description', sa.String(512), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_merchant_description_patterns_merchant_id', 'finbot_merchant_description_patterns', ['merchant_id'])
    op.create_unique_constraint(
        'uidx_merchant_description_patterns_merchant_desc',
        'finbot_merchant_description_patterns',
        ['merchant_id', 'sanitized_description'],
    )

    op.add_column(
        'finbot_transactions_history',
        sa.Column('merchant_id', sa.Integer(), sa.ForeignKey('finbot_merchants.id', ondelete='SET NULL')),
    )
    op.create_index('idx_transactions_history_merchant', 'finbot_transactions_history', ['merchant_id'])


def downgrade():
    op.drop_index('idx_transactions_history_merchant', table_name='finbot_transactions_history')
    op.drop_column('finbot_transactions_history', 'merchant_id')
    op.drop_table('finbot_merchant_description_patterns')
    op.drop_table('finbot_merchants')
