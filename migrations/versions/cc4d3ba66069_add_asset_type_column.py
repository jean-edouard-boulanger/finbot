"""add asset_type column

Revision ID: cc4d3ba66069
Revises: bf91ce936b11
Create Date: 2023-10-07 08:45:04.963956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc4d3ba66069'
down_revision = 'bf91ce936b11'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("finbot_sub_accounts_items_snapshot_entries", sa.Column("asset_class", sa.String(length=32)))
    op.add_column("finbot_sub_accounts_items_valuation_history_entries", sa.Column("asset_class", sa.String(length=32)))


def downgrade():
    op.drop_column("finbot_sub_accounts_items_snapshot_entries", "asset_class")
    op.drop_column("finbot_sub_accounts_items_valuation_history_entries", "asset_class")
