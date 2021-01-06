"""include created_at/updated_at UserAccountPlaidSettings

Revision ID: 55acd2598fc5
Revises: 4ff5c47e587d
Create Date: 2021-01-03 13:49:45.647113

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55acd2598fc5'
down_revision = '4ff5c47e587d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('finbot_user_accounts_plaid_settings', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('finbot_user_accounts_plaid_settings', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('finbot_user_accounts_plaid_settings', 'updated_at')
    op.drop_column('finbot_user_accounts_plaid_settings', 'created_at')
    # ### end Alembic commands ###