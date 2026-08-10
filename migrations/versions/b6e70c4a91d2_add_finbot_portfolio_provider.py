"""add finbot portfolio provider

Revision ID: b6e70c4a91d2
Revises: a2d5c9e13f74
Create Date: 2026-08-10 18:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b6e70c4a91d2'
down_revision = 'a2d5c9e13f74'
branch_labels = None
depends_on = None


# Finbot managed portfolios are linked accounts backed by the `finbot_portfolio` provider, which
# only existed in the hydration data file: databases created before portfolios were introduced are
# never re-hydrated, so the provider row has to be backfilled here.
def upgrade():
    op.execute(
        """
        INSERT INTO finbot_providers (id, description, website_url, credentials_schema, created_at)
        VALUES (
            'finbot_portfolio',
            'Finbot managed portfolio',
            'https://github.com/jeanedouard-boulanger/finbot',
            '{"json_schema": {}}',
            now()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade():
    # The provider row is only removed when nothing depends on it: the linked accounts foreign key
    # cascades on delete, and dropping it would take live portfolio accounts down with it.
    op.execute(
        """
        DELETE FROM finbot_providers
        WHERE id = 'finbot_portfolio'
        AND NOT EXISTS (
            SELECT 1 FROM finbot_linked_accounts WHERE provider_id = 'finbot_portfolio'
        )
        """
    )
