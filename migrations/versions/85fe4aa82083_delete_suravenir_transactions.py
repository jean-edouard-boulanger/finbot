"""delete suravenir transactions

Revision ID: 85fe4aa82083
Revises: b3f7a2c91d04
Create Date: 2026-03-14 06:50:02.973077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85fe4aa82083'
down_revision = 'b3f7a2c91d04'
branch_labels = None
depends_on = None

PROVIDER_ID = "suravenir_fr"


def upgrade():
    conn = op.get_bind()

    # Delete transaction matches referencing suravenir_fr transactions
    conn.execute(sa.text("""
        DELETE FROM finbot_transaction_matches
        WHERE outflow_transaction_id IN (
            SELECT th.id FROM finbot_transactions_history th
            JOIN finbot_linked_accounts la ON la.id = th.linked_account_id
            WHERE la.provider_id = :provider_id
        )
        OR inflow_transaction_id IN (
            SELECT th.id FROM finbot_transactions_history th
            JOIN finbot_linked_accounts la ON la.id = th.linked_account_id
            WHERE la.provider_id = :provider_id
        )
    """), {"provider_id": PROVIDER_ID})

    # Delete transaction history entries
    conn.execute(sa.text("""
        DELETE FROM finbot_transactions_history
        WHERE linked_account_id IN (
            SELECT id FROM finbot_linked_accounts
            WHERE provider_id = :provider_id
        )
    """), {"provider_id": PROVIDER_ID})

    # Delete transaction snapshot entries
    conn.execute(sa.text("""
        DELETE FROM finbot_transactions_snapshot_entries
        WHERE linked_account_snapshot_entry_id IN (
            SELECT las.id FROM finbot_linked_accounts_snapshots las
            JOIN finbot_linked_accounts la ON la.id = las.linked_account_id
            WHERE la.provider_id = :provider_id
        )
    """), {"provider_id": PROVIDER_ID})


def downgrade():
    # Data deletion cannot be reversed
    pass
