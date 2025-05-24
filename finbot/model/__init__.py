import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Type, TypeVar

import orjson
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from finbot.core.db.types import DateTimeTz, JSONEncoded
from finbot.core.utils import some

if TYPE_CHECKING:
    from sqlalchemy.sql.type_api import TypeEngine

    T = TypeVar("T")

    class Enum(TypeEngine[T]):
        def __init__(self, arg: Type[T], **kwargs: Any) -> None:
            pass

else:
    from sqlalchemy import Enum


Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "finbot_user_accounts"
    id = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False, unique=True)
    password_hash = Column(LargeBinary, nullable=False)
    full_name = Column(String(128), nullable=False)
    mobile_phone_number = Column(String(128))
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    linked_accounts = relationship(
        "LinkedAccount",
        back_populates="user_account",
        uselist=True,
        passive_deletes=True,
    )
    settings = relationship(
        "UserAccountSettings",
        uselist=False,
        back_populates="user_account",
        passive_deletes=True,
    )
    snapshots = relationship(
        "UserAccountSnapshot",
        uselist=True,
        back_populates="user_account",
        passive_deletes=True,
    )
    history_entries = relationship(
        "UserAccountHistoryEntry",
        uselist=True,
        back_populates="user_account",
        passive_deletes=True,
    )


class UserAccountSettings(Base):
    __tablename__ = "finbot_user_accounts_settings"
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), primary_key=True)
    valuation_ccy = Column(String(3), nullable=False)
    schedule_valuation = Column(Boolean, nullable=False, server_default=expression.true(), default=True)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False, back_populates="settings")

    def serialize(self) -> dict[str, Any]:
        return {
            "valuation_ccy": self.valuation_ccy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Provider(Base):
    __tablename__ = "finbot_providers"
    id = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=False)
    website_url = Column(String(256), nullable=False)
    credentials_schema = Column(JSONEncoded, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    linked_accounts = relationship("LinkedAccount", uselist=True)

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "website_url": self.website_url,
            "credentials_schema": self.credentials_schema,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class LinkedAccount(Base):
    __tablename__ = "finbot_linked_accounts"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), nullable=False)
    provider_id = Column(String(64), ForeignKey(Provider.id, ondelete="CASCADE"), nullable=False)
    account_name = Column(String(256), nullable=False)
    account_colour = Column(String(10), nullable=False)
    selected_sub_accounts = Column(ARRAY(String), nullable=True)
    encrypted_credentials = Column(Text)
    deleted = Column(Boolean, nullable=False, default=False)
    frozen = Column(Boolean, nullable=False, default=False, server_default=expression.false())
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False, back_populates="linked_accounts")

    provider = relationship("Provider", uselist=False)

    __table_args__ = (
        UniqueConstraint(
            user_account_id,
            provider_id,
            account_name,
            name="uidx_linked_accounts_user_provider_account_name",
        ),
    )

    @property
    def plain_credentials(self) -> Any:
        from finbot.core import environment, secure

        return orjson.loads(
            secure.fernet_decrypt(
                some(self.encrypted_credentials).encode(),
                environment.get_secret_key().encode(),
            ).decode()
        )


class SnapshotStatus(enum.Enum):
    Pending = 1
    Processing = 2
    Success = 3
    Failure = 4


class UserAccountSnapshot(Base):
    __tablename__ = "finbot_user_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), nullable=False)
    status = Column(Enum(SnapshotStatus), nullable=False)
    requested_ccy = Column(String(3), nullable=False)
    start_time = Column(DateTimeTz, index=True)
    end_time = Column(DateTimeTz, index=True)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False)
    xccy_rates_entries = relationship(
        "XccyRateSnapshotEntry",
        back_populates="snapshot",
        uselist=True,
        passive_deletes=True,
    )
    linked_accounts_entries = relationship(
        "LinkedAccountSnapshotEntry",
        back_populates="snapshot",
        uselist=True,
        passive_deletes=True,
    )

    @property
    def effective_at(self) -> Optional[datetime]:
        return self.end_time


class XccyRateSnapshotEntry(Base):
    __tablename__ = "finbot_xccy_rates_snapshots"
    snapshot_id = Column(
        Integer,
        ForeignKey(UserAccountSnapshot.id, ondelete="CASCADE"),
        primary_key=True,
    )
    xccy_pair = Column(String(6), primary_key=True)
    rate = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(UserAccountSnapshot, uselist=False, back_populates="xccy_rates_entries")


class LinkedAccountSnapshotEntry(Base):
    __tablename__ = "finbot_linked_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="CASCADE"))
    linked_account_id = Column(Integer, ForeignKey("finbot_linked_accounts.id", ondelete="CASCADE"))
    success = Column(Boolean, nullable=False)
    failure_details = Column(JSONEncoded)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(UserAccountSnapshot, uselist=False, back_populates="linked_accounts_entries")
    linked_account = relationship(LinkedAccount, uselist=False)
    sub_accounts_entries = relationship(
        "SubAccountSnapshotEntry",
        back_populates="linked_account_entry",
        passive_deletes=True,
    )


class SubAccountSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_snapshot_entries"
    id = Column(Integer, primary_key=True)
    linked_account_snapshot_entry_id = Column(Integer, ForeignKey(LinkedAccountSnapshotEntry.id, ondelete="CASCADE"))
    sub_account_id = Column(String(64), nullable=False)
    sub_account_ccy = Column(String(3), nullable=False)
    sub_account_description = Column(String(256), nullable=False)
    sub_account_type = Column(String(32), nullable=False)
    sub_account_sub_type = Column(String(32))
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    linked_account_entry = relationship(
        LinkedAccountSnapshotEntry, uselist=False, back_populates="sub_accounts_entries"
    )
    items_entries = relationship(
        "SubAccountItemSnapshotEntry", back_populates="sub_account_entry", passive_deletes=True
    )


class SubAccountItemType(enum.Enum):
    Asset = 1
    Liability = 2


class SubAccountItemSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_items_snapshot_entries"
    id = Column(Integer, primary_key=True)
    sub_account_snapshot_entry_id = Column(
        Integer,
        ForeignKey(SubAccountSnapshotEntry.id, ondelete="CASCADE"),
        nullable=False,
    )
    item_type = Column(Enum(SubAccountItemType), nullable=False)
    name = Column(String(256), nullable=False)
    item_subtype = Column(String(32), nullable=False)
    asset_class = Column(String(32))
    asset_type = Column(String(32))
    units = Column(Numeric)
    value_sub_account_ccy = Column(Numeric)
    value_snapshot_ccy = Column(Numeric)
    value_item_ccy = Column(Numeric)
    currency = Column(String(4))
    isin_code = Column(String(16))
    provider_specific_data = Column(JSONEncoded)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    sub_account_entry = relationship(SubAccountSnapshotEntry, uselist=False, back_populates="items_entries")


class ValuationChangeEntry(Base):
    __tablename__ = "finbot_valuation_change_entries"
    id = Column(Integer, primary_key=True)
    change_1hour = Column(Numeric)
    change_1day = Column(Numeric)
    change_1week = Column(Numeric)
    change_1month = Column(Numeric)
    change_6months = Column(Numeric)
    change_1year = Column(Numeric)
    change_2years = Column(Numeric)

    def serialize(self) -> dict[str, Any]:
        return {
            "change_1hour": self.change_1hour,
            "change_1day": self.change_1day,
            "change_1week": self.change_1week,
            "change_1month": self.change_1month,
            "change_6months": self.change_6months,
            "change_1year": self.change_1year,
            "change_2years": self.change_2years,
        }


class UserAccountHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_history_entries"
    id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id, ondelete="CASCADE"), nullable=False)
    source_snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="SET NULL"))
    valuation_ccy = Column(String(3), nullable=False)
    effective_at = Column(DateTimeTz, nullable=False, index=True)
    available = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False)
    source_snapshot = relationship(UserAccountSnapshot, uselist=False)
    user_account_valuation_history_entry = relationship(
        "UserAccountValuationHistoryEntry",
        back_populates="account_valuation_history_entry",
        uselist=False,
    )
    linked_accounts_valuation_history_entries = relationship(
        "LinkedAccountValuationHistoryEntry",
        back_populates="account_valuation_history_entry",
        uselist=True,
        passive_deletes=True,
    )
    sub_accounts_valuation_history_entries = relationship(
        "SubAccountValuationHistoryEntry",
        back_populates="account_valuation_history_entry",
        uselist=True,
        passive_deletes=True,
    )
    sub_accounts_items_valuation_history_entries = relationship(
        "SubAccountItemValuationHistoryEntry",
        back_populates="account_valuation_history_entry",
        uselist=True,
        passive_deletes=True,
    )


class UserAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_valuation_history_entries"
    history_entry_id = Column(
        Integer,
        ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"),
        primary_key=True,
    )
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="user_account_valuation_history_entry",
    )

    @property
    def total_assets(self) -> float:
        return float(self.valuation - self.total_liabilities)


class LinkedAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_linked_accounts_valuation_history_entries"
    history_entry_id = Column(
        Integer,
        ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"),
        primary_key=True,
    )
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    effective_snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id, ondelete="SET NULL"))
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    effective_snapshot = relationship(UserAccountSnapshot, uselist=False)
    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="linked_accounts_valuation_history_entries",
    )

    @property
    def total_assets(self) -> float:
        return float(self.valuation - self.total_liabilities)


class SubAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_sub_accounts_valuation_history_entries"
    history_entry_id = Column(
        Integer,
        ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"),
        primary_key=True,
    )
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    sub_account_id = Column(String(64), primary_key=True)
    sub_account_ccy = Column(String(3), nullable=False)
    sub_account_description = Column(String(256), nullable=False)
    sub_account_type = Column(String(32), nullable=False)
    sub_account_sub_type = Column(String(32))
    valuation = Column(Numeric, nullable=False)
    total_liabilities = Column(Numeric, nullable=False, server_default="0.0")
    valuation_sub_account_ccy = Column(Numeric, nullable=False)
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_valuation_history_entries",
    )
    sub_accounts_items_valuation_history_entries = relationship(
        "SubAccountItemValuationHistoryEntry",
        back_populates="sub_account_valuation_history_entry",
    )

    @property
    def total_assets(self) -> float:
        return float(self.valuation - self.total_liabilities)


class SubAccountItemValuationHistoryEntry(Base):
    __tablename__ = "finbot_sub_accounts_items_valuation_history_entries"
    history_entry_id = Column(
        Integer,
        ForeignKey(UserAccountHistoryEntry.id, ondelete="CASCADE"),
        primary_key=True,
    )
    linked_account_id = Column(Integer, ForeignKey(LinkedAccount.id, ondelete="CASCADE"), primary_key=True)
    sub_account_id = Column(String(64), primary_key=True)
    item_type = Column(Enum(SubAccountItemType), primary_key=True)
    name = Column(String(256), primary_key=True)
    item_subtype = Column(String(32), nullable=False)
    asset_class = Column(String(32))
    asset_type = Column(String(32))
    units = Column(Numeric)
    valuation = Column(Numeric, nullable=False)
    valuation_sub_account_ccy = Column(Numeric, nullable=False)
    valuation_item_ccy = Column(Numeric)
    valuation_change_id = Column(Integer, ForeignKey(ValuationChangeEntry.id, ondelete="SET NULL"))
    currency = Column(String(4))
    isin_code = Column(String(16))
    provider_specific_data = Column(JSONEncoded)
    created_at = Column(DateTimeTz, server_default=func.now(), nullable=False)
    updated_at = Column(DateTimeTz, onupdate=func.now())

    valuation_change = relationship(ValuationChangeEntry, uselist=False)
    linked_account = relationship(LinkedAccount, uselist=False)
    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_items_valuation_history_entries",
    )
    sub_account_valuation_history_entry = relationship(
        SubAccountValuationHistoryEntry,
        uselist=False,
        back_populates="sub_accounts_items_valuation_history_entries",
        viewonly=True,
        foreign_keys=[history_entry_id, linked_account_id, sub_account_id],
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["history_entry_id", "linked_account_id", "sub_account_id"],
            [
                SubAccountValuationHistoryEntry.history_entry_id,
                SubAccountValuationHistoryEntry.linked_account_id,
                SubAccountValuationHistoryEntry.sub_account_id,
            ],
        ),
    )

    @property
    def is_asset(self) -> bool:
        return self.item_type == SubAccountItemType.Asset

    @property
    def is_liability(self) -> bool:
        return self.item_type == SubAccountItemType.Liability


class GenericKeyValueStore(Base):
    __tablename__ = "finbot_generic_key_value_store"
    key = Column(String(64), primary_key=True)
    value = Column(JSONEncoded, nullable=False)
