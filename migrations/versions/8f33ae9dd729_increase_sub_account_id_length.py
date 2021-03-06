"""Increase sub_account_id length

Revision ID: 8f33ae9dd729
Revises: 55acd2598fc5
Create Date: 2021-01-06 22:12:11.954929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f33ae9dd729'
down_revision = '55acd2598fc5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('finbot_sub_accounts_items_valuation_history_entries', 'sub_account_id',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=64))
    op.alter_column('finbot_sub_accounts_snapshot_entries', 'sub_account_id',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=64),
               existing_nullable=False)
    op.alter_column('finbot_sub_accounts_valuation_history_entries', 'sub_account_id',
               existing_type=sa.VARCHAR(length=32),
               type_=sa.String(length=64))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('finbot_sub_accounts_valuation_history_entries', 'sub_account_id',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=32))
    op.alter_column('finbot_sub_accounts_snapshot_entries', 'sub_account_id',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=32),
               existing_nullable=False)
    op.alter_column('finbot_sub_accounts_items_valuation_history_entries', 'sub_account_id',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=32))
    # ### end Alembic commands ###
