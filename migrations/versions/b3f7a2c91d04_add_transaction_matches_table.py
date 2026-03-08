"""add transaction_matches table

Revision ID: b3f7a2c91d04
Revises: 888bc7a190a0
Create Date: 2026-03-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f7a2c91d04'
down_revision = '888bc7a190a0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'finbot_transaction_matches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_account_id', sa.Integer(), sa.ForeignKey('finbot_user_accounts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('outflow_transaction_id', sa.Integer(), sa.ForeignKey('finbot_transactions_history.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('inflow_transaction_id', sa.Integer(), sa.ForeignKey('finbot_transactions_history.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('match_confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('match_status', sa.String(16), nullable=False, server_default='auto'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint('outflow_transaction_id != inflow_transaction_id', name='ck_transaction_matches_different_txns'),
    )
    op.create_index(
        'idx_transaction_matches_user_status',
        'finbot_transaction_matches',
        ['user_account_id', 'match_status'],
    )


def downgrade():
    op.drop_index('idx_transaction_matches_user_status', table_name='finbot_transaction_matches')
    op.drop_table('finbot_transaction_matches')
