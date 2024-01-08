"""add sub_account_sub_type to SubAccountSnapshotEntry

Revision ID: 3574c0452805
Revises: a28d5f66588f
Create Date: 2024-01-08 17:05:33.070624

"""
from alembic import op
import sqlalchemy as sa

from finbot.providers.schema import AccountType

# revision identifiers, used by Alembic.
revision = '3574c0452805'
down_revision = 'a28d5f66588f'
branch_labels = None
depends_on = None


sub_account_type_mapping = {
    "cash": AccountType.depository,
    "lending": AccountType.investment,
    "pension": AccountType.investment,
    "unknown": AccountType.other,
}


def upgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_snapshot_entries ADD COLUMN IF NOT EXISTS sub_account_sub_type VARCHAR(32) NULL DEFAULT NULL")
    op.execute("ALTER TABLE finbot_sub_accounts_valuation_history_entries ADD COLUMN IF NOT EXISTS sub_account_sub_type VARCHAR(32) NULL DEFAULT NULL")
    conn = op.get_bind()
    for table_name in ("finbot_sub_accounts_snapshot_entries", "finbot_sub_accounts_valuation_history_entries"):
        for old_asset_type, new_asset_type in sub_account_type_mapping.items():
            conn.execute(sa.text(
                f""" UPDATE {table_name}
                       SET sub_account_type = :new_asset_type
                     WHERE sub_account_type = :old_asset_type
                """
            ), {"old_asset_type": old_asset_type, "new_asset_type": new_asset_type.value})
            conn.commit()


def downgrade():
    op.execute("ALTER TABLE finbot_sub_accounts_snapshot_entries DROP COLUMN IF EXISTS sub_account_sub_type")
    op.execute("ALTER TABLE finbot_sub_accounts_valuation_history_entries DROP COLUMN IF EXISTS sub_account_sub_type")
