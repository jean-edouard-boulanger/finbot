"""add is_demo to user account model

Revision ID: 23924d787025
Revises: eee41b0dd64a
Create Date: 2024-07-29 13:30:19.869012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23924d787025'
down_revision = 'eee41b0dd64a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("finbot_user_accounts", sa.Column("is_demo", sa.Boolean(), nullable=False, server_default="false"))


def downgrade():
    op.drop_column("finbot_user_accounts", "is_demo")
