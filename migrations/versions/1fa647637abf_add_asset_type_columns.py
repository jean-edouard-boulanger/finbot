"""add asset_type columns

Revision ID: 1fa647637abf
Revises: cc4d3ba66069
Create Date: 2023-10-08 07:09:12.118056

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fa647637abf'
down_revision = 'cc4d3ba66069'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("finbot_sub_accounts_items_snapshot_entries", sa.Column("asset_type", sa.String(length=32)))
    op.add_column("finbot_sub_accounts_items_valuation_history_entries", sa.Column("asset_type", sa.String(length=32)))


def downgrade():
    op.drop_column("finbot_sub_accounts_items_snapshot_entries", "asset_type")
    op.drop_column("finbot_sub_accounts_items_valuation_history_entries", "asset_type")
