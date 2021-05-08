"""add mobile number

Revision ID: 0213400aeb85
Revises: b97ac7612883
Create Date: 2021-04-09 21:11:05.756151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0213400aeb85'
down_revision = 'b97ac7612883'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('finbot_user_accounts', sa.Column('mobile_phone_number', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('finbot_user_accounts', 'mobile_phone_number')
    # ### end Alembic commands ###
