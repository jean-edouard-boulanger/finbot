"""rename underlying_ccy to currency

Revision ID: 185f0bdef74f
Revises: 22578cf02898
Create Date: 2024-01-05 07:33:39.702825

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '185f0bdef74f'
down_revision = '22578cf02898'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries RENAME COLUMN underlying_ccy TO currency")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries RENAME COLUMN underlying_ccy TO currency")


def downgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_items_snapshot_entries RENAME COLUMN currency TO underlying_ccy")
    op.execute("ALTER TABLE finbot_sub_accounts_items_valuation_history_entries RENAME COLUMN currency TO underlying_ccy")
