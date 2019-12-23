CREATE TABLE finbot_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    encrypted_password VARCHAR(100) NOT NULL,
    salt VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);

CREATE TABLE finbot_providers (
    id VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE finbot_users_accounts (
    user_id INTEGER REFERENCES finbot_users(id) NOT NULL,
    provider_id VARCHAR(50) REFERENCES finbot_providers(id) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    encryped_credentials_blob BYTEA NOT NULL,
    PRIMARY KEY(user_id, provider_id, account_name)
);

CREATE TYPE snapshot_status AS ENUM ('pending', 'started', 'finished', 'failure');

CREATE TABLE finbot_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES finbot_users(id) NOT NULL,
    status snapshot_status NOT NULL,
    requested_ccy CHAR(4) NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    failures_count INTEGER,
    success_count INTEGER
);

CREATE TABLE finbot_snapshots_xccy_rates (
    snapshot_id INTEGER REFERENCES finbot_snapshots(id),
    xccy VARCHAR(6) NOT NULL,
    rate NUMERIC NOT NULL
);

CREATE TABLE finbot_accounts_snapshots (
    snapshot_id INTEGER REFERENCES finbot_snapshots(id),
    provider_id INTEGER NOT NULL,
    provider_description VARCHAR(255) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    amount_snapshot_ccy NUMERIC NOT NULL,
    overall_weight NUMERIC NOT NULL
);

CREATE TABLE finbot_sub_accounts_snapshots (
    snapshot_id INTEGER REFERENCES finbot_snapshots(id),
    provider_id INTEGER NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    sub_account_name VARCHAR(100) NOT NULL,
    sub_account_id VARCHAR(100) NOT NULL,
    sub_account_ccy CHAR(4) NOT NULL,
    amount_snapshot_ccy NUMERIC NOT NULL,
    account_weight NUMERIC NOT NULL,
    overall_weight NUMERIC NOT NULL
);

CREATE TABLE finbot_assets_snapshots (
    snapshot_id INTEGER REFERENCES finbot_snapshots(id) NOT NULL,
    provider_id INTEGER NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    sub_account_name VARCHAR(100) NOT NULL,
    sub_account_id VARCHAR(100) NOT NULL,
    sub_account_ccy CHAR(4) NOT NULL,
    asset_name VARCHAR(255) NOT NULL,
    asset_type VARCHAR(12) NOT NULL,
    units NUMERIC,
    amount_sub_account_ccy NUMERIC NOT NULL,
    amount_snapshot_ccy NUMERIC NOT NULL,
    sub_account_weight NUMERIC NOT NULL,
    account_weight NUMERIC NOT NULL,
    overall_weight NUMERIC NOT NULL,
    provider_specific_blob BYTEA
);
