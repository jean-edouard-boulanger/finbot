from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    Text,
    ForeignKey,
    UniqueConstraint,
    Enum,
    func
)
import enum
import json


class JSONEncoded(TypeDecorator):
    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


DateTimeTz = DateTime(timezone=True)
Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "finbot_user_accounts"
    id = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    full_name = Column(String(128), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())
    
    linked_accounts = relationship("LinkedAccount", back_populates="user_account")
    settings = relationship(
        "UserAccountSettings", 
        uselist=False, 
        back_populates="user_account")


class UserAccountSettings(Base):
    __tablename__ = "finbot_user_accounts_settings"
    user_account_id = Column(Integer, ForeignKey(UserAccount.id), primary_key=True)
    valuation_ccy = Column(String(3), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(
        UserAccount, 
        uselist=False, 
        back_populates="settings")


class Provider(Base):
    __tablename__ = "finbot_providers"
    id = Column(String(64), primary_key=True)
    description = Column(String(256), nullable=False)
    website_url = Column(String(256), nullable=False)
    credentials_schema = Column(JSONEncoded, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())


class LinkedAccount(Base):
    __tablename__ = "finbot_linked_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(UserAccount.id), nullable=False)
    provider_id = Column(String(64), ForeignKey(Provider.id), nullable=False)
    account_name = Column(String(64), nullable=False)
    encrypted_credentials = Column(Text)
    deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(
        UserAccount, 
        uselist=False, 
        back_populates="linked_accounts")
    
    provider = relationship("Provider", uselist=False)

    __table_args__ = (
        UniqueConstraint(
            user_id, provider_id, account_name,
            name="uidx_linked_accounts_user_provider_account_name"),
    )


class SnapshotStatus(enum.Enum):
    Pending = 1
    Processing = 2
    Success = 3
    Failure = 4


class UserAccountSnapshot(Base):
    __tablename__ = "finbot_user_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(SnapshotStatus), nullable=False)
    requested_ccy = Column(String(3), nullable=False)
    start_time = Column(DateTimeTz)
    end_time = Column(DateTimeTz)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    xccy_rates_entries = relationship(
        "XccyRateSnapshotEntry", 
        back_populates="snapshot")

    linked_accounts_entries = relationship(
        "LinkedAccountSnapshotEntry", 
        back_populates="snapshot")


class XccyRateSnapshotEntry(Base):
    __tablename__ = "finbot_xccy_rates_snapshots"
    snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id), primary_key=True)
    xccy_pair = Column(String(6), primary_key=True)
    rate = Column(Numeric, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(
        UserAccountSnapshot, 
        uselist=False, 
        back_populates="xccy_rates_entries")


class LinkedAccountSnapshotEntry(Base):
    __tablename__ = "finbot_linked_accounts_snapshots"
    entry_id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id))
    linked_account_id = Column(Integer, ForeignKey("finbot_linked_accounts.id"))
    success = Column(Boolean, nullable=False)
    failure_details = Column(JSONEncoded)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    snapshot = relationship(
        UserAccountSnapshot, 
        uselist=False, 
        back_populates="linked_accounts_entries")
    
    sub_accounts_entries = relationship(
        "SubAccountSnapshotEntry", 
        back_populates="linked_account_entry")


class SubAccountSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_snapshots"
    entry_id = Column(Integer, primary_key=True)
    linked_account_snapshot_entry_id = Column(Integer, ForeignKey(LinkedAccountSnapshotEntry.entry_id))
    sub_account_id = Column(String(32), nullable=False)
    sub_account_ccy = Column(String(3), nullable=False)
    sub_account_description = Column(String(256), nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    linked_account_entry = relationship(
        LinkedAccountSnapshotEntry, 
        uselist=False, 
        back_populates="sub_accounts_entries")
    
    items_entries = relationship(
        "SubAccountItemSnapshotEntry", 
        back_populates="sub_account_entry")


class SubAccountItemType(enum.Enum):
    Asset = 1
    Liability = 2


class SubAccountItemSnapshotEntry(Base):
    __tablename__ = "finbot_sub_accounts_items_snapshots"
    entry_id = Column(Integer, primary_key=True)
    sub_account_snapshot_entry_id = Column(Integer, ForeignKey(SubAccountSnapshotEntry.entry_id), nullable=False)
    item_type = Column(Enum(SubAccountItemType), nullable=False)
    name = Column(String(256), nullable=False)
    item_subtype = Column(String(32), nullable=False)
    units = Column(Numeric)
    value_sub_account_ccy = Column(Numeric)
    value_snapshot_ccy = Column(Numeric)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    sub_account_entry = relationship(
        SubAccountSnapshotEntry, 
        uselist=False, 
        back_populates="items_entries")


class UserAccountHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_history_entries"
    entry_id = Column(Integer, primary_key=True)
    user_account_id = Column(Integer, ForeignKey(UserAccount.id))
    source_snapshot_id = Column(Integer, ForeignKey(UserAccountSnapshot.id))
    effective_at = Column(DateTimeTz, nullable=False)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    user_account = relationship(UserAccount, uselist=False)
    source_snapshot = relationship(UserAccountSnapshot, uselist=False)
    valuation_history_entry = relationship(
        "UserAccountValuationHistoryEntry", 
        uselist=False, 
        back_populates="account_valuation_history_entry")


class UserAccountValuationHistoryEntry(Base):
    __tablename__ = "finbot_user_accounts_valuation_history_entries"
    history_entry_id = Column(Integer, ForeignKey(UserAccountHistoryEntry.entry_id), primary_key=True)
    valuation_ccy = Column(String(3), nullable=False)
    valuation_date = Column(Date, nullable=False)
    change_1hour = Column(Numeric)
    change_1day = Column(Numeric)
    change_1week = Column(Numeric)
    change_1month = Column(Numeric)
    change_6months = Column(Numeric)
    change_1year = Column(Numeric)
    change_all_time = Column(Numeric)
    created_at = Column(DateTimeTz, server_default=func.now())
    updated_at = Column(DateTimeTz, onupdate=func.now())

    account_valuation_history_entry = relationship(
        UserAccountHistoryEntry, 
        uselist=False, 
        back_populates="valuation_history_entry")
