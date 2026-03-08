"""drop transaction_category column from transactions history

Revision ID: 888bc7a190a0
Revises: 6ed999372bf3
Create Date: 2026-03-08 08:34:09.328084

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '888bc7a190a0'
down_revision = '6ed999372bf3'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('finbot_transactions_history', 'transaction_category')


def downgrade():
    op.add_column(
        'finbot_transactions_history',
        sa.Column('transaction_category', sa.String(16), nullable=False, server_default='other'),
    )
