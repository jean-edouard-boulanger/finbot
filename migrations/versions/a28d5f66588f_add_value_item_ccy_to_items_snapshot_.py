"""add value_item_ccy to items snapshot/history

Revision ID: a28d5f66588f
Revises: 185f0bdef74f
Create Date: 2024-01-08 09:46:03.987571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a28d5f66588f'
down_revision = '185f0bdef74f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries ADD COLUMN IF NOT EXISTS value_item_ccy NUMERIC NULL DEFAULT NULL")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries ADD COLUMN IF NOT EXISTS valuation_item_ccy NUMERIC NULL DEFAULT NULL")


def downgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries DROP COLUMN IF EXISTS value_item_ccy")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries DROP COLUMN IF EXISTS valuation_item_ccy")
