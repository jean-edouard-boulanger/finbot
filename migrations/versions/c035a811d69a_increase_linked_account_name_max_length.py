"""increase linked account name max length

Revision ID: c035a811d69a
Revises: 8f33ae9dd729
Create Date: 2021-02-06 09:13:24.649627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c035a811d69a'
down_revision = '8f33ae9dd729'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('finbot_linked_accounts', 'account_name',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=256),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('finbot_linked_accounts', 'account_name',
               existing_type=sa.String(length=256),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False)
    # ### end Alembic commands ###