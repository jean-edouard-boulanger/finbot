"""add schedule_valuation setting

Revision ID: ca5140aa19db
Revises: b51af3f5240c
Create Date: 2023-12-18 19:13:36.665392

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'ca5140aa19db'
down_revision = 'b51af3f5240c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE finbot_user_accounts_settings 
        ADD COLUMN IF NOT EXISTS schedule_valuation BOOLEAN NOT NULL DEFAULT TRUE
    """)


def downgrade():
    op.execute("""
        ALTER TABLE finbot_user_accounts_settings
        DROP COLUMN IF EXISTS schedule_valuation
    """)
