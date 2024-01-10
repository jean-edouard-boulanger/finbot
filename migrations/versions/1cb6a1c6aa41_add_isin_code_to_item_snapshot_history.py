"""add isin_code to item snapshot/history

Revision ID: 1cb6a1c6aa41
Revises: 3574c0452805
Create Date: 2024-01-09 09:00:53.068188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cb6a1c6aa41'
down_revision = '3574c0452805'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries ADD COLUMN IF NOT EXISTS isin_code VARCHAR(16) NULL DEFAULT NULL")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries ADD COLUMN IF NOT EXISTS isin_code VARCHAR(16) NULL DEFAULT NULL")


def downgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries DROP COLUMN IF EXISTS isin_code")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries DROP COLUMN IF EXISTS isin_code")
