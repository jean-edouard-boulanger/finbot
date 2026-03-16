"""add recurring group description

Revision ID: e9b4f2a7c1d3
Revises: d7a1e3f5b2c8
Create Date: 2026-03-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e9b4f2a7c1d3'
down_revision = 'd7a1e3f5b2c8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'finbot_recurring_transaction_groups',
        sa.Column('description', sa.Text()),
    )


def downgrade():
    op.drop_column('finbot_recurring_transaction_groups', 'description')
