"""add recurring transaction groups

Revision ID: d7a1e3f5b2c8
Revises: c4e8f1a2b3d5
Create Date: 2026-03-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = 'd7a1e3f5b2c8'
down_revision = 'c4e8f1a2b3d5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'finbot_recurring_transaction_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_account_id', sa.Integer(), sa.ForeignKey('finbot_user_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('merchant_id', sa.Integer(), sa.ForeignKey('finbot_merchants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('currency', sa.String(4), nullable=False),
        sa.Column('avg_amount', sa.Numeric(), nullable=False),
        sa.Column('avg_interval_days', sa.Numeric(), nullable=False),
        sa.Column('transaction_count', sa.Integer(), nullable=False),
        sa.Column('total_spent', sa.Numeric(), nullable=False),
        sa.Column('total_spent_ccy', sa.Numeric()),
        sa.Column('first_seen', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('last_seen', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP(timezone=True)),
    )
    op.create_index('idx_recurring_groups_user_account', 'finbot_recurring_transaction_groups', ['user_account_id'])
    op.create_index('idx_recurring_groups_merchant', 'finbot_recurring_transaction_groups', ['merchant_id'])

    op.add_column(
        'finbot_transactions_history',
        sa.Column('recurring_group_id', sa.Integer(), sa.ForeignKey('finbot_recurring_transaction_groups.id', ondelete='SET NULL')),
    )
    op.create_index('idx_transactions_history_recurring_group', 'finbot_transactions_history', ['recurring_group_id'])


def downgrade():
    op.drop_index('idx_transactions_history_recurring_group', table_name='finbot_transactions_history')
    op.drop_column('finbot_transactions_history', 'recurring_group_id')
    op.drop_index('idx_recurring_groups_merchant', table_name='finbot_recurring_transaction_groups')
    op.drop_index('idx_recurring_groups_user_account', table_name='finbot_recurring_transaction_groups')
    op.drop_table('finbot_recurring_transaction_groups')
