"""add linked account colour

Revision ID: 73e4a88e4e69
Revises: 75027cc0f5c9
Create Date: 2023-10-15 11:25:48.870391

"""
from alembic import op
from itertools import cycle
import sqlalchemy as sa
import random

from finbot.apps.appwsrv.core.formatting_rules import ACCOUNTS_PALETTE


# revision identifiers, used by Alembic.
revision = '73e4a88e4e69'
down_revision = '75027cc0f5c9'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE finbot_linked_accounts ADD COLUMN IF NOT EXISTS account_colour VARCHAR(10) NULL DEFAULT NULL")
    conn = op.get_bind()
    colour_picker = cycle(ACCOUNTS_PALETTE)
    results = conn.execute(sa.text("SELECT id FROM finbot_linked_accounts ORDER BY user_account_id"))
    for row in results.fetchall():
        conn.execute(
            sa.text("UPDATE finbot_linked_accounts SET account_colour = :colour WHERE id = :linked_account_id"),
            {"colour": next(colour_picker), "linked_account_id": row[0]}
        )
    conn.commit()
    op.execute("ALTER TABLE finbot_linked_accounts ALTER COLUMN account_colour SET NOT NULL")


def downgrade():
    op.execute("ALTER TABLE finbot_linked_accounts DROP COLUMN IF EXISTS account_colour")
