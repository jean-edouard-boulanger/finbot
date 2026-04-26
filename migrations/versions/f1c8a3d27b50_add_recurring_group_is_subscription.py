"""add recurring group is_subscription

Revision ID: f1c8a3d27b50
Revises: e9b4f2a7c1d3
Create Date: 2026-04-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1c8a3d27b50'
down_revision = 'e9b4f2a7c1d3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'finbot_recurring_transaction_groups',
        sa.Column('is_subscription', sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_column('finbot_recurring_transaction_groups', 'is_subscription')
