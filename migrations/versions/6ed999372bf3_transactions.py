"""transactions

Revision ID: 6ed999372bf3
Revises: 23924d787025
Create Date: 2026-03-02 10:37:05.217010

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = '6ed999372bf3'
down_revision = '23924d787025'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'finbot_transactions_snapshot_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('linked_account_snapshot_entry_id', sa.Integer(),
                   sa.ForeignKey('finbot_linked_accounts_snapshots.id', ondelete='CASCADE'),
                   nullable=False),
        sa.Column('transaction_count', sa.Integer(), nullable=False),
        sa.Column('transactions_data', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        'finbot_transactions_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('linked_account_id', sa.Integer(),
                   sa.ForeignKey('finbot_linked_accounts.id', ondelete='CASCADE'),
                   nullable=False),
        sa.Column('sub_account_id', sa.String(64), nullable=False),
        sa.Column('provider_transaction_id', sa.String(256), nullable=False),
        sa.Column('transaction_date', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('transaction_type', sa.String(32), nullable=False),
        sa.Column('transaction_category', sa.String(16), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('amount_snapshot_ccy', sa.Numeric()),
        sa.Column('currency', sa.String(4), nullable=False),
        sa.Column('description', sa.String(512), nullable=False),
        sa.Column('symbol', sa.String(64)),
        sa.Column('units', sa.Numeric()),
        sa.Column('unit_price', sa.Numeric()),
        sa.Column('fee', sa.Numeric()),
        sa.Column('counterparty', sa.String(256)),
        sa.Column('spending_category_primary', sa.String(64)),
        sa.Column('spending_category_detailed', sa.String(128)),
        sa.Column('spending_category_source', sa.String(16)),
        sa.Column('provider_specific_data', sa.Text()),
        sa.Column('source_snapshot_id', sa.Integer(),
                   sa.ForeignKey('finbot_user_accounts_snapshots.id', ondelete='SET NULL')),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True)),
        sa.UniqueConstraint(
            'linked_account_id', 'sub_account_id', 'provider_transaction_id',
            name='uidx_transactions_history_dedup',
        ),
        sa.Index('idx_transactions_history_account_date', 'linked_account_id', 'transaction_date'),
        sa.Index('idx_transactions_history_date', 'transaction_date'),
    )


def downgrade():
    op.drop_table('finbot_transactions_history')
    op.drop_table('finbot_transactions_snapshot_entries')
