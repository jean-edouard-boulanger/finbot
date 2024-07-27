"""add selected_sub_accounts to finbot_linked_accounts

Revision ID: eee41b0dd64a
Revises: 1cb6a1c6aa41
Create Date: 2024-07-27 05:51:32.797955

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eee41b0dd64a'
down_revision = '1cb6a1c6aa41'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("finbot_linked_accounts", sa.Column('selected_sub_accounts', sa.ARRAY(sa.String), nullable=True))


def downgrade():
    op.drop_column("finbot_linked_accounts", "selected_sub_accounts")
