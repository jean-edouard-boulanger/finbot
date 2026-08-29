"""add notifications

Revision ID: f3c07b5a9e21
Revises: c4a8d1f60b93
Create Date: 2026-08-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3c07b5a9e21'
down_revision = 'c4a8d1f60b93'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'finbot_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_account_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(64), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('dedup_key', sa.String(128), nullable=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('payload', sa.VARCHAR(), nullable=True),
        sa.Column('occurrences', sa.Integer(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_account_id'], ['finbot_user_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    # Aggregation invariant: at most one un-dismissed notification per (user, dedup_key). The predicate is
    # deliberately only `dismissed_at IS NULL` -- adding `status = 'active'` would let a resolved-but-undismissed
    # row fall out of the index, so a recurring problem would insert a second row alongside the resolved one.
    # NULL dedup_keys never conflict in a btree, so non-aggregated notifications insert freely.
    op.create_index(
        'uidx_notifications_user_account_dedup_key',
        'finbot_notifications',
        ['user_account_id', 'dedup_key'],
        unique=True,
        postgresql_where=sa.text('dismissed_at IS NULL'),
    )
    op.create_index(
        'idx_notifications_user_account_created_at',
        'finbot_notifications',
        ['user_account_id', 'created_at'],
    )


def downgrade():
    op.drop_index('idx_notifications_user_account_created_at', table_name='finbot_notifications')
    op.drop_index('uidx_notifications_user_account_dedup_key', table_name='finbot_notifications')
    op.drop_table('finbot_notifications')
