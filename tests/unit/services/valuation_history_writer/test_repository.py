import pytest
from datetime import timedelta
from decimal import Decimal

from finbot.core.utils import now_utc
from finbot.core.db.session import Session as DBSession
from finbot.providers.schema import AssetType, AssetClass
from finbot.services.valuation_history_writer.repository import (
    ReportRepository,
    ConsistencySnapshotItemEntry,
    ConsistentSnapshot,
    ConsistencySnapshotEmptySubAccountEntry,
)
from finbot.model import (
    UserAccount,
    UserAccountSettings,
    LinkedAccount,
    UserAccountSnapshot,
    Provider,
    SnapshotStatus,
    LinkedAccountSnapshotEntry,
    SubAccountSnapshotEntry,
    SubAccountItemSnapshotEntry,
    SubAccountItemType,
)


@pytest.fixture(scope="function")
def sample_provider(
    db_session: DBSession,
) -> Provider:
    provider: Provider
    with db_session.persist(Provider()) as provider:
        provider.id = "test_bank_fr"
        provider.description = "Test provider"
        provider.website_url = "https://test-bank.fr"
        provider.credentials_schema = {}
    return provider


@pytest.fixture(scope="function")
def sample_user_account(
    db_session: DBSession,
) -> UserAccount:
    user_account: UserAccount
    with db_session.persist(UserAccount()) as user_account:
        user_account.email = "test@finbot.com"
        user_account.password_hash = b"fake password hash"
        user_account.full_name = "Test Account"
        user_account.mobile_phone_number = "0000"
        user_account.settings = UserAccountSettings(valuation_ccy="EUR")
    return user_account


@pytest.fixture(scope="function")
def sample_linked_accounts(
    sample_user_account: UserAccount,
    sample_provider: Provider,
    db_session: DBSession,
) -> list[LinkedAccount]:
    linked_accounts = [
        LinkedAccount(
            user_account_id=sample_user_account.id,
            provider_id=sample_provider.id,
            account_name=f"Test account {i}",
            encrypted_credentials="",
        )
        for i in range(2)
    ]
    db_session.add_all(linked_accounts)
    db_session.commit()
    return linked_accounts


@pytest.fixture(scope="function")
def sample_previous_snapshot(
    sample_user_account: UserAccount,
    sample_linked_accounts: list[LinkedAccount],
    db_session: DBSession,
) -> UserAccountSnapshot:
    snapshot: UserAccountSnapshot
    with db_session.persist(UserAccountSnapshot()) as snapshot:
        snapshot.user_account_id = sample_user_account.id
        snapshot.status = SnapshotStatus.Success
        snapshot.requested_ccy = sample_user_account.settings.valuation_ccy
        snapshot.start_time = now_utc() - timedelta(days=1)
        snapshot.end_time = now_utc() - timedelta(days=1)
        snapshot.linked_accounts_entries = [
            LinkedAccountSnapshotEntry(
                linked_account_id=sample_linked_accounts[0].id,
                success=True,
                sub_accounts_entries=[
                    SubAccountSnapshotEntry(
                        sub_account_id="SA_TEST_01",
                        sub_account_ccy="EUR",
                        sub_account_description="My test account 01",
                        sub_account_type="depository",
                        items_entries=[
                            SubAccountItemSnapshotEntry(
                                item_type=SubAccountItemType.Asset,
                                name="EUR",
                                item_subtype="currency",
                                asset_class=AssetClass.currency.value,
                                asset_type=AssetType.cash.value,
                                value_sub_account_ccy=1000.0,
                                value_snapshot_ccy=1000.0,
                                provider_specific_data={},
                            )
                        ],
                    ),
                    SubAccountSnapshotEntry(
                        sub_account_id="SA_TEST_02",
                        sub_account_ccy="EUR",
                        sub_account_description="My test account 02 (empty)",
                        sub_account_type="investment",
                        items_entries=[],
                    ),
                ],
            ),
            LinkedAccountSnapshotEntry(
                linked_account_id=sample_linked_accounts[1].id,
                success=True,
                sub_accounts_entries=[
                    SubAccountSnapshotEntry(
                        sub_account_id="SA_TEST_03",
                        sub_account_ccy="USD",
                        sub_account_description="My test account 03",
                        sub_account_type="investment",
                        items_entries=[
                            SubAccountItemSnapshotEntry(
                                item_type=SubAccountItemType.Asset,
                                name="EUR",
                                item_subtype="currency",
                                asset_class=AssetClass.foreign_currency.value,
                                asset_type=AssetType.cash.value,
                                value_sub_account_ccy=500.0,
                                value_snapshot_ccy=474.0,
                            ),
                            SubAccountItemSnapshotEntry(
                                item_type=SubAccountItemType.Asset,
                                name="Test Fund",
                                item_subtype="equity",
                                asset_class=AssetClass.equities.value,
                                asset_type=AssetType.ETF.value,
                                value_sub_account_ccy=1500.0,
                                value_snapshot_ccy=1422.0,
                            ),
                        ],
                    )
                ],
            ),
        ]
    return snapshot


@pytest.fixture(scope="function")
def sample_last_snapshot(
    sample_user_account: UserAccount,
    sample_linked_accounts: list[LinkedAccount],
    db_session: DBSession,
) -> UserAccountSnapshot:
    snapshot: UserAccountSnapshot
    with db_session.persist(UserAccountSnapshot()) as snapshot:
        snapshot.user_account_id = sample_user_account.id
        snapshot.status = SnapshotStatus.Success
        snapshot.requested_ccy = sample_user_account.settings.valuation_ccy
        snapshot.start_time = now_utc()
        snapshot.end_time = now_utc()
        snapshot.linked_accounts_entries = [
            LinkedAccountSnapshotEntry(
                linked_account_id=sample_linked_accounts[0].id,
                success=True,
                sub_accounts_entries=[
                    SubAccountSnapshotEntry(
                        sub_account_id="SA_TEST_01",
                        sub_account_ccy="EUR",
                        sub_account_description="My test account 01",
                        sub_account_type="depository",
                        items_entries=[
                            SubAccountItemSnapshotEntry(
                                item_type=SubAccountItemType.Asset,
                                name="EUR",
                                item_subtype="currency",
                                asset_class=AssetClass.currency.value,
                                asset_type=AssetType.cash.value,
                                units=100.0,
                                value_sub_account_ccy=1000.0,
                                value_snapshot_ccy=1000.0,
                            ),
                        ],
                    ),
                    SubAccountSnapshotEntry(
                        sub_account_id="SA_TEST_02",
                        sub_account_ccy="EUR",
                        sub_account_description="My test account 02 (empty)",
                        sub_account_type="investment",
                        items_entries=[],
                    ),
                ],
            ),
            LinkedAccountSnapshotEntry(
                linked_account_id=sample_linked_accounts[1].id,
                success=False,
            ),
        ]
    return snapshot


def test_get_consistent_snapshot_data(
    db_session: DBSession,
    sample_previous_snapshot: UserAccountSnapshot,
    sample_last_snapshot: UserAccountSnapshot,
):
    repository = ReportRepository(db_session)
    consistent_snapshot_data = repository.get_consistent_snapshot_data(
        snapshot_id=sample_last_snapshot.id
    )
    assert consistent_snapshot_data == ConsistentSnapshot(
        snapshot_data=[
            ConsistencySnapshotItemEntry(
                snapshot_id=1,
                linked_account_snapshot_entry_id=2,
                linked_account_id=2,
                sub_account_id="SA_TEST_03",
                sub_account_ccy="USD",
                sub_account_description="My test account 03",
                sub_account_type="investment",
                item_name="EUR",
                item_type=SubAccountItemType.Asset,
                item_subtype="currency",
                item_asset_class="foreign_currency",
                item_asset_type="cash",
                item_units=None,
                value_snapshot_ccy=Decimal(474.0),
                value_sub_account_ccy=Decimal(500.0),
                item_provider_specific_data=None,
            ),
            ConsistencySnapshotItemEntry(
                snapshot_id=1,
                linked_account_snapshot_entry_id=2,
                linked_account_id=2,
                sub_account_id="SA_TEST_03",
                sub_account_ccy="USD",
                sub_account_description="My test account 03",
                sub_account_type="investment",
                item_name="Test Fund",
                item_type=SubAccountItemType.Asset,
                item_subtype="equity",
                item_asset_class="equities",
                item_asset_type="ETF",
                item_units=None,
                value_snapshot_ccy=Decimal(1422.0),
                value_sub_account_ccy=Decimal(1500.0),
                item_provider_specific_data=None,
            ),
            ConsistencySnapshotItemEntry(
                snapshot_id=2,
                linked_account_snapshot_entry_id=3,
                linked_account_id=1,
                sub_account_id="SA_TEST_01",
                sub_account_ccy="EUR",
                sub_account_description="My test account 01",
                sub_account_type="depository",
                item_name="EUR",
                item_type=SubAccountItemType.Asset,
                item_subtype="currency",
                item_asset_class="currency",
                item_asset_type="cash",
                item_units=Decimal(100.0),
                value_snapshot_ccy=Decimal(1000.0),
                value_sub_account_ccy=Decimal(1000.0),
                item_provider_specific_data=None,
            ),
            ConsistencySnapshotEmptySubAccountEntry(
                snapshot_id=2,
                linked_account_snapshot_entry_id=3,
                linked_account_id=1,
                sub_account_id="SA_TEST_02",
                sub_account_ccy="EUR",
                sub_account_description="My test account 02 (empty)",
                sub_account_type="investment",
            ),
        ]
    )
