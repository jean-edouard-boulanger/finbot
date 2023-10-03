"""drop twilio settings column

Revision ID: bf91ce936b11
Revises: 764a6f372b53
Create Date: 2023-10-03 15:15:41.080133

"""
from alembic import op
import sqlalchemy as sa

from finbot.core.db.types import JSONEncoded


# revision identifiers, used by Alembic.
revision = 'bf91ce936b11'
down_revision = '764a6f372b53'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('finbot_user_accounts_settings', 'twilio_settings')


def downgrade():
    op.add_column('finbot_user_accounts_settings', sa.Column('twilio_settings', JSONEncoded(), nullable=True))
