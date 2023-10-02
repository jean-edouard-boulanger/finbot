"""drop user account plaid settings

Revision ID: 764a6f372b53
Revises: bbce6d728c64
Create Date: 2023-10-02 12:05:41.159618

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '764a6f372b53'
down_revision = 'bbce6d728c64'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('finbot_user_accounts_plaid_settings')


def downgrade():
    op.create_table('finbot_user_accounts_plaid_settings',
    sa.Column('user_account_id', sa.Integer(), nullable=False),
    sa.Column('env', sa.String(length=32), nullable=False),
    sa.Column('client_id', sa.String(length=64), nullable=False),
    sa.Column('public_key', sa.String(length=64), nullable=False),
    sa.Column('secret_key', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['user_account_id'], ['finbot_user_accounts.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_account_id')
    )
