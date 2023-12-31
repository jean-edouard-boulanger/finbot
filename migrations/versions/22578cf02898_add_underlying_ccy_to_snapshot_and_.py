"""add underlying ccy to snapshot and history item

Revision ID: 22578cf02898
Revises: ca5140aa19db
Create Date: 2023-12-31 12:05:08.579385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22578cf02898'
down_revision = 'ca5140aa19db'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries ADD COLUMN IF NOT EXISTS underlying_ccy VARCHAR(5) NULL DEFAULT NULL")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries ADD COLUMN IF NOT EXISTS underlying_ccy VARCHAR(5) NULL DEFAULT NULL")


def downgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries DROP COLUMN IF EXISTS underlying_ccy")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries DROP COLUMN IF EXISTS underlying_ccy")
