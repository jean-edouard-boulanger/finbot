from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Boolean, 
    DateTime,
    Numeric,
    LargeBinary,
    ForeignKey,
    UniqueConstraint,
    Enum
)
import enum


Base = declarative_base()


class User(Base):
    __tablename__ = "finbot_users"
    id = Column(Integer, primary_key=True)
    email = Column(String(128), nullable=False)
    encrypted_password = Column(String(64), nullable=False)
    password_salt = Column(String(64), nullable=False)
    full_name = Column(String(128), nullable=False)
    valuation_ccy = Column(String(3), nullable=False)
    registered_accounts = relationship("RegisteredAccount", back_populates="user")


class Provider(Base):
    __tablename__ = "finbot_providers"
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(32), nullable=False)
    description = Column(String(256), nullable=False)


class ExternalAccount(Base):
    __tablename__ = "finbot_external_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("finbot_users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("finbot_providers.id"), nullable=False)
    account_name = Column(String(64), nullable=False)
    encryped_credentials_blob = Column(LargeBinary)
    deleted = Column(Boolean, nullable=False, default=False)
    user = relationship("User", back_populates="external_accounts")
    provider = relationship("Provider")
    __table_args__ = (
        UniqueConstraint(
            user_id, provider_id, account_name,
            name="uidx_external_accounts_user_provider_account_name"),
    )


class SnapshotStatus(enum.Enum):
    pending = 1
    processing = 2
    success = 3
    failure = 4


class Snapshot(Base):
    __tablename__ = "finbot_snapshots"
    id = Column(Integer, primary_key=True)
    status = Column(Enum(SnapshotStatus), nullable=False)
    requested_ccy = Column(String(3), nullable=False)
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    xccy_rates = relationship("SnapshotXccyRate", back_populates="snapshot")


class XccyRateSnapshot(Base):
    __tablename__ = "finbot_xccy_rates_snapshots"
    snapshot_id = Column(Integer, ForeignKey("finbot_snapshots.id"), primary_key=True)
    xccy = Column(String(6), primary_key=True)
    rate = Column(Numeric, nullable=False)
    snapshot = relationship("Snapshot", back_populates="xccy_rates")


class AccountSnapshot(Base):
    __tablename__ = "finbot_accounts_snapshots"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("finbot_snapshots.id"))
    external_account_id = Column(Integer, ForeignKey("finbot_external_accounts.id"))
    hist_provider_name = Column(String(32), nullable=False)
    hist_provider_description = Column(String(256), nullable=False)
    hist_account_name = Column(String(64), nullable=False)
    value_snapshot_ccy = Column(Numeric, nullable=False)
    overall_weight = Column(Numeric, nullable=False)
