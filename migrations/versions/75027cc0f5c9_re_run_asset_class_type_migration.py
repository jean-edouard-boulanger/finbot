"""re run asset class type migration

Revision ID: 75027cc0f5c9
Revises: a188f4998b21
Create Date: 2023-10-08 12:49:43.713849

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy import text
from finbot.providers.schema import AssetClass, AssetType


# revision identifiers, used by Alembic.
revision = '75027cc0f5c9'
down_revision = 'a188f4998b21'
branch_labels = None
depends_on = None


GENERIC_UPDATES_MAPPING = [
    {"item_subtype": "commodity", "asset_class": AssetClass.commodities, "asset_type": AssetType.precious_metal},
    {"item_subtype": "equity fund", "asset_class": AssetClass.equities, "asset_type": AssetType.ETF},
    {"item_subtype": "blended fund", "asset_class": AssetClass.multi_asset, "asset_type": AssetType.generic_fund},
    {"item_subtype": "cryptocurrency", "asset_class": AssetClass.crypto, "asset_type": AssetType.crypto_currency},
    {"item_subtype": "loan", "asset_class": AssetClass.private_debt, "asset_type": AssetType.loan},
    {"item_subtype": "equity option", "asset_class": AssetClass.equities, "asset_type": AssetType.option},
]


def upgrade():
    conn = op.get_bind()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = null,
               asset_type = null
    """))
    for entry in GENERIC_UPDATES_MAPPING:
        conn.execute(text(f"""
            UPDATE finbot_sub_accounts_items_valuation_history_entries
               SET asset_class = :asset_class,
                   asset_type = :asset_type
             WHERE item_subtype = :item_subtype
        """), {
            "asset_class": entry["asset_class"].value,
            "asset_type": entry["asset_type"].value,
            "item_subtype": entry["item_subtype"]
        })
        conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.equities.value}',
               asset_type = '{AssetType.stock.value}'
         WHERE item_subtype = 'equity'
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.equities.value}',
               asset_type = '{AssetType.ETF.value}'
         WHERE item_subtype = 'equity'
               AND name LIKE '%ETF%'
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.equities.value}',
               asset_type = '{AssetType.ETN.value}'
         WHERE item_subtype = 'equity'
               AND name LIKE '%ETN%'
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.multi_asset.value}',
               asset_type = '{AssetType.generic_fund.value}'
         WHERE item_subtype = 'currency'
           AND name = 'AVIVA ACTIF GARANTI'
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.currency.value}',
               asset_type = '{AssetType.cash.value}'
         WHERE item_subtype IN ('Currency', 'currency')
           AND valuation_sub_account_ccy = valuation
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = '{AssetClass.foreign_currency.value}',
               asset_type = '{AssetType.cash.value}'
         WHERE item_subtype IN ('Currency', 'currency')
           AND valuation_sub_account_ccy != valuation
    """))
    conn.commit()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET item_subtype = 'currency'
         WHERE item_subtype = 'Currency'
    """))
    conn.commit()

def downgrade():
    conn = op.get_bind()
    conn.execute(text(f"""
        UPDATE finbot_sub_accounts_items_valuation_history_entries
           SET asset_class = null,
               asset_type = null
    """))
