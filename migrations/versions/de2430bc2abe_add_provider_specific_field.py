"""add provider specific field

Revision ID: de2430bc2abe
Revises: 4305433d5c7a
Create Date: 2023-04-15 08:08:02.771106

"""
from finbot.core.db.types import JSONEncoded
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'de2430bc2abe'
down_revision = '4305433d5c7a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('finbot_sub_accounts_items_snapshot_entries', sa.Column('provider_specific_data', JSONEncoded(), nullable=True))
    op.add_column('finbot_sub_accounts_items_valuation_history_entries', sa.Column('provider_specific_data', JSONEncoded(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('finbot_sub_accounts_items_valuation_history_entries', 'provider_specific_data')
    op.drop_column('finbot_sub_accounts_items_snapshot_entries', 'provider_specific_data')
    # ### end Alembic commands ###
