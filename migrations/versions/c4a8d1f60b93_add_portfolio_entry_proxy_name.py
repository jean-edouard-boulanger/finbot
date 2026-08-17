"""add portfolio entry proxy name

Revision ID: c4a8d1f60b93
Revises: b6e70c4a91d2
Create Date: 2026-08-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4a8d1f60b93'
down_revision = 'b6e70c4a91d2'
branch_labels = None
depends_on = None


def upgrade():
    # Resolving a security's display name costs a second call to Yahoo Finance, so it is kept
    # alongside the symbol rather than looked up whenever a portfolio is displayed. Entries tracked
    # before this column existed fill it in the next time their symbol is set.
    op.add_column('finbot_portfolio_entries', sa.Column('proxy_name', sa.String(256)))


def downgrade():
    op.drop_column('finbot_portfolio_entries', 'proxy_name')
