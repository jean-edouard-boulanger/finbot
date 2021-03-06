from typing import List
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload, contains_eager
from sqlalchemy.exc import IntegrityError

from finbot.clients.finbot import FinbotClient
from finbot.apps.appwsrv import timeseries, repository, core
from finbot.apps.appwsrv.reports import holdings as holdings_report
from finbot.apps.appwsrv.reports import earnings as earnings_report
from finbot.apps.support import request_handler, Route, ApplicationError
from finbot.core.utils import serialize, now_utc
from finbot.core import secure
from finbot.core import dbutils
from finbot.model import (
    Provider,
    UserAccount,
    UserAccountSettings,
    UserAccountPlaidSettings,
    LinkedAccount,
    UserAccountHistoryEntry,
    LinkedAccountValuationHistoryEntry,
    DistributedTrace
)

import logging.config
import logging
import json
import os


logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


SECRET = open(os.environ["FINBOT_SECRET_PATH"], "r").read()
FINBOT_FINBOTWSRV_ENDPOINT = os.environ["FINBOT_FINBOTWSRV_ENDPOINT"]


def get_finbot_client():
    return FinbotClient(FINBOT_FINBOTWSRV_ENDPOINT)


logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s (%(threadName)s) [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://sys.stdout',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})


db_engine = create_engine(os.environ['FINBOT_DB_URL'])
db_session = dbutils.add_persist_utilities(scoped_session(sessionmaker(bind=db_engine)))


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = str(SECRET)

CORS(app)
JWTManager(app)


@app.teardown_appcontext
def cleanup_context(*args, **kwargs):
    db_session.remove()


API_V1 = Route("/api/v1")


ADMIN = API_V1.admin


@app.route(ADMIN.traces.p("guid")(), methods=["GET"])
def get_traces(guid):
    traces = db_session.query(DistributedTrace).filter_by(guid=guid).all()
    return jsonify(serialize({
        "traces": [
            trace
            for trace in traces
        ]
    }))


AUTH = API_V1.auth


@app.route(AUTH.login(), methods=["POST"])
@request_handler(schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["email", "password"],
    "properties": {
        "email": {"type": "string"},
        "password": {"type": "string"}
    }
})
def auth_login():
    data = request.json
    account = db_session.query(UserAccount).filter_by(email=data["email"]).first()
    if not account:
        raise ApplicationError("Invalid email or password")
    
    # TODO: password should be hashed, not encrypted/decrypted with secret
    account_password = secure.fernet_decrypt(
        account.encrypted_password.encode(), SECRET.encode()).decode()
    if account_password != data["password"]:
        raise ApplicationError("Invalid email or password")

    # TODO: expires_delta should be set to a reasonable time interval
    return jsonify({
        "auth": {
            "access_token": create_access_token(identity=account.id, expires_delta=False),
            "refresh_token": create_refresh_token(identity=account.id, expires_delta=False),
        },
        "account": {
            "id": account.id,
            "email": account.email,
            "full_name": account.full_name,
            "created_at": account.created_at,
            "updated_at": account.updated_at
        }
    })


@app.route(API_V1.providers(), methods=["PUT"])
@request_handler(schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "description", "website_url", "credentials_schema"],
    "properties": {
        "id": {"type": "string"},
        "description": {"type": "string"},
        "website_url": {"type": "string"},
        "credentials_schema": {"type": "object"}
    }
})
def update_or_create_provider():
    data = request.json
    existing_provider = repository.find_provider(db_session, data["id"])
    with db_session.persist(existing_provider or Provider()) as provider:
        provider.id = data["id"]
        provider.description = data["description"]
        provider.website_url = data["website_url"]
        provider.credentials_schema = data["credentials_schema"]
    return jsonify(provider.serialize())


@app.route(API_V1.providers(), methods=["GET"])
@request_handler()
def get_providers():
    providers = db_session.query(Provider).all()
    return jsonify(serialize({
        "providers": [provider for provider in providers]
    }))


@app.route(API_V1.providers.p("provider_id")(), methods=["GET"])
@request_handler()
def get_provider(provider_id: str):
    provider = repository.find_provider(db_session, provider_id)
    if not provider:
        raise ApplicationError(f"Provider with id '${provider_id}' does not exist")
    return jsonify(serialize(provider))


@app.route(API_V1.providers.p("provider_id")(), methods=["DELETE"])
@request_handler()
def delete_provider(provider_id: str):
    provider = repository.find_provider(db_session, provider_id)
    if not Provider:
        raise ApplicationError(f"Provider with id '${provider_id}' does not exist")
    linked_accounts: List[LinkedAccount] = provider.linked_accounts
    if len(linked_accounts) > 0:
        raise ApplicationError("This provider is still in use")
    db_session.delete(provider)
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return jsonify({})


ACCOUNTS = API_V1.accounts


@app.route(ACCOUNTS(), methods=["POST"])
@request_handler(trace_values=False, schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["email", "password", "full_name", "settings"],
    "properties": {
        "email": {"type": "string"},
        "password": {"type": "string"},
        "full_name": {"type": "string"},
        "settings": {
            "type": "object",
            "required": ["valuation_ccy"],
            "properties": {
                "valuation_ccy": {"type": "string"}
            }
        }
    }
})
def create_user_account():
    data = request.json
    try:
        with db_session.persist(UserAccount()) as user_account:
            user_account.email = data["email"]
            user_account.encrypted_password = secure.fernet_encrypt(
                    data["password"].encode(), SECRET).decode()
            user_account.full_name = data["full_name"]
            user_account.settings = UserAccountSettings(
                valuation_ccy=data["settings"]["valuation_ccy"])
    except IntegrityError as e:
        logging.warning(f"failed to create user account: {e}")
        raise ApplicationError(f"User account with email '{user_account.email}' already exists")

    return jsonify({
        "user_account": {
            "id": user_account.id,
            "email": user_account.email,
            "full_name": user_account.full_name,
            "settings": {
                "valuation_ccy": user_account.settings.valuation_ccy,
                "created_at": user_account.settings.created_at,
                "updated_at": user_account.settings.updated_at
            },
            "created_at": user_account.created_at,
            "updated_at": user_account.updated_at
        }
    })


ACCOUNT = ACCOUNTS.p("user_account_id")


def serialize_use_account_valuation(entry: UserAccountHistoryEntry,
                                    history: List[UserAccountHistoryEntry],
                                    sparkline_schedule: List[datetime]):
    valuation_entry = entry.user_account_valuation_history_entry
    return {
        "history_entry_id": entry.id,
        "date": entry.effective_at,
        "currency": entry.valuation_ccy,
        "value": valuation_entry.valuation,
        "total_liabilities": valuation_entry.total_liabilities,
        "change": valuation_entry.valuation_change,
        "sparkline": [
            {
                "effective_at": valuation_time,
                "value": uas_v.user_account_valuation_history_entry.valuation
                if uas_v is not None else None
            }
            for valuation_time, uas_v in timeseries.schedulify(
                sparkline_schedule, history,
                lambda uas_v: uas_v.effective_at)
        ]
    }


@app.route(ACCOUNT.is_configured())
@jwt_required
@request_handler()
def is_user_account_configured(user_account_id: int):
    account = repository.get_user_account(db_session, user_account_id)
    configured = len(account.linked_accounts) > 0
    return jsonify({
        "configured": configured
    })


@app.route(ACCOUNT(), methods=["GET"])
@jwt_required
@request_handler()
def get_user_account(user_account_id):
    account = repository.get_user_account(db_session, user_account_id)
    to_time = now_utc()
    from_time = to_time - timedelta(days=30)
    valuation_history = repository.find_user_account_historical_valuation(
        session=db_session,
        user_account_id=user_account_id,
        from_time=from_time, to_time=to_time)
    sparkline_schedule = timeseries.create_schedule(
        from_time=from_time,
        to_time=to_time,
        frequency=timeseries.ScheduleFrequency.Daily)

    valuation = valuation_history[-1] if len(valuation_history) > 0 else None

    return jsonify(serialize({
        "result": {
            "user_account": {
                "id": account.id,
                "email": account.email,
                "full_name": account.full_name,
                "settings": account.settings,
                "created_at": account.created_at,
                "updated_at": account.updated_at
            },
            "valuation": serialize_use_account_valuation(valuation, valuation_history, sparkline_schedule)
            if valuation else None
        }
    }))


@app.route(ACCOUNT.settings(), methods=["GET"])
@jwt_required
@request_handler()
def get_user_account_settings(user_account_id):
    settings = db_session.query(UserAccountSettings).filter_by(user_account_id=user_account_id).first()
    plaid_settings = db_session.query(UserAccountPlaidSettings).filter_by(user_account_id=user_account_id).first()

    return jsonify(serialize({
        "settings": {
            "settings": settings,
            "plaid_settings": plaid_settings
        }
    }))


@app.route(ACCOUNT.history(), methods=["GET"])
@jwt_required
@request_handler()
def get_user_account_valuation_history(user_account_id):
    history_entries = (db_session.query(UserAccountHistoryEntry)
                                 .filter_by(user_account_id=user_account_id)
                                 .filter_by(available=True)
                                 .order_by(asc(UserAccountHistoryEntry.effective_at))
                                 .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry,
                                                     innerjoin=True))
                                 .all())

    return jsonify(serialize({
        "historical_valuation": [
                {
                    "date": entry.effective_at,
                    "currency": entry.valuation_ccy,
                    "value": entry.user_account_valuation_history_entry.valuation
                }
                for entry in timeseries.sample_time_series(
                    history_entries,
                    time_getter=(lambda item: item.effective_at),
                    interval=timedelta(days=1))
        ]
    }))


@app.route(ACCOUNT.linked_accounts(), methods=["GET"])
@jwt_required
@request_handler()
def get_linked_accounts(user_account_id):
    results = repository.find_linked_accounts(db_session, user_account_id)
    return jsonify(serialize({
        "linked_accounts": [
            {
                "id": entry.id,
                "account_name": entry.account_name,
                "deleted": entry.deleted,
                "provider": entry.provider,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at
            }
            for entry in results
        ]
    }))


@app.route(ACCOUNT.linked_accounts.valuation(), methods=["GET"])
@jwt_required
@request_handler()
def get_linked_accounts_valuation(user_account_id):
    history_entry = repository.find_last_history_entry(db_session, user_account_id)
    if not history_entry:
        raise ApplicationError("No data to report")
    results = repository.find_linked_accounts_valuation(db_session, history_entry.id)
    return jsonify(serialize({
        "linked_accounts": [
            {
                "linked_account": {
                    "id": entry.linked_account.id,
                    "provider_id": entry.linked_account.provider_id,
                    "description": entry.linked_account.account_name,
                },
                "valuation": {
                    "date": (entry.effective_snapshot.effective_at
                             if entry.effective_snapshot
                             else history_entry.effective_at),
                    "currency": history_entry.valuation_ccy,
                    "value": entry.valuation,
                    "change": entry.valuation_change
                }
            }
            for entry in results
            if not entry.linked_account.deleted
        ]
    }))


@app.route(ACCOUNT.linked_accounts(), methods=["POST"])
@jwt_required
@request_handler(trace_values=False, schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["provider_id", "credentials", "account_name"],
    "properties": {
        "provider_id": {"type": "string"},
        "credentials": {"type": ["null", "object"]},
        "account_name": {"type": "string"}
    }
})
def create_linked_account(user_account_id):
    do_validate = bool(int(request.args.get("validate", 1)))
    do_persist = bool(int(request.args.get("persist", 1)))
    request_data = request.json

    logging.info(f"validate={do_validate} persist={do_persist}")

    user_account = (db_session.query(UserAccount)
                              .filter_by(id=user_account_id)
                              .options(joinedload(UserAccount.plaid_settings))
                              .first())

    if not user_account:
        raise ApplicationError(f"could not find user account with id '{user_account_id}'")

    provider_id = request_data["provider_id"]
    provider = (db_session.query(Provider)
                          .filter_by(id=provider_id)
                          .first())

    if not provider:
        raise ApplicationError(f"could not find provider with id '{provider_id}'")

    is_plaid = provider.id == "plaid_us"
    if is_plaid and not user_account.plaid_settings:
        raise ApplicationError("user account is not setup for Plaid")

    credentials = request_data["credentials"]
    if is_plaid:
        credentials = core.make_plaid_credentials(
            credentials, user_account.plaid_settings)
        logging.info(credentials)

    if do_validate:
        logging.info(f"validating authentication details for "
                     f"account_id={user_account_id} and provider_id={provider_id}")
        core.validate_credentials(
            finbot_client=get_finbot_client(),
            plaid_settings=user_account.plaid_settings,
            provider_id=provider_id,
            credentials=credentials)

    if do_persist:
        logging.info(f"Linking external account (provider_id={provider.id}) to user account_id={user_account.id}")
        try:
            with db_session.persist(user_account):
                encrypted_credentials = secure.fernet_encrypt(
                    json.dumps(credentials).encode(), SECRET).decode()
                user_account.linked_accounts.append(
                    LinkedAccount(
                        provider_id=request_data["provider_id"],
                        account_name=request_data["account_name"],
                        encrypted_credentials=encrypted_credentials))
        except IntegrityError:
            raise ApplicationError(f"Provider '{provider.description}' was already linked "
                                   f"as '{request_data['account_name']}' in this account")

    return jsonify({
        "result": {
            "validated": do_validate,
            "persisted": do_persist
        }
    })


LINKED_ACCOUNT = ACCOUNT.linked_accounts.p("linked_account_id")


@app.route(LINKED_ACCOUNT(), methods=["PUT"])
@jwt_required
@request_handler(trace_values=False, schema={
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "provider_id": {"type": "string"},
        "credentials": {"type": ["null", "object"]},
        "account_name": {"type": "string"}
    }
})
def update_linked_account(user_account_id, linked_account_id):
    request_data = request.json
    linked_account_id = int(linked_account_id)
    linked_account = repository.find_linked_account(db_session, user_account_id, linked_account_id)

    if not linked_account:
        raise ApplicationError(f"could not find linked account with id '{linked_account_id}'")

    new_provider_id = request_data.get("provider_id", linked_account.provider_id)
    request_provider_update = "provider_id" in request_data and new_provider_id != linked_account.provider_id
    request_has_credentials = "credentials" in request_data

    if request_provider_update and not request_has_credentials:
        raise ApplicationError("new credentials must be provided when updating provider")

    credentials_need_validating = request_has_credentials or request_provider_update

    if credentials_need_validating:
        logging.info(f"validating authentication details for "
                     f"account_id={user_account_id} and provider_id={new_provider_id}")
        core.validate_credentials(get_finbot_client(), new_provider_id, request_data["credentials"])

    try:
        with db_session.persist(linked_account):
            linked_account.provider_id = new_provider_id
            if "account_name" in request_data:
                linked_account.account_name = request_data["account_name"]
            if request_has_credentials:
                encrypted_credentials = secure.fernet_encrypt(
                    json.dumps(request_data["credentials"]).encode(), SECRET).decode()
                linked_account.encrypted_credentials = encrypted_credentials
    except IntegrityError as e:
        raise ApplicationError(str(e))

    return jsonify({})


@app.route(LINKED_ACCOUNT(), methods=["DELETE"])
@jwt_required
@request_handler()
def delete_linked_account(user_account_id, linked_account_id):
    linked_account_id = int(linked_account_id)
    linked_account = repository.find_linked_account(db_session, user_account_id, linked_account_id)
    if not linked_account:
        raise ApplicationError(f"could not find linked account with id '{linked_account_id}'")

    with db_session.persist(linked_account):
        linked_account.deleted = True

    return jsonify({})


@app.route(LINKED_ACCOUNT.history(), methods=["GET"])
@jwt_required
@request_handler()
def get_linked_account_historical_valuation(user_account_id, linked_account_id):
    linked_account_id = int(linked_account_id)
    results = (db_session.query(UserAccountHistoryEntry)
                         .filter_by(user_account_id=user_account_id)
                         .filter_by(available=True)
                         .join(UserAccountHistoryEntry.linked_accounts_valuation_history_entries)
                         .options(
                             contains_eager(UserAccountHistoryEntry.linked_accounts_valuation_history_entries))
                         .filter(LinkedAccountValuationHistoryEntry.linked_account_id == linked_account_id)
                         .order_by(desc(UserAccountHistoryEntry.effective_at))
                         .all())

    output_entries = []
    for account_entry in results:
        assert len(account_entry.linked_accounts_valuation_history_entries) == 1
        for entry in account_entry.linked_accounts_valuation_history_entries:
            assert entry.linked_account_id == linked_account_id
            output_entries.append({
                    "linked_account_id": entry.linked_account_id,
                    "date": account_entry.effective_at,
                    "currency": account_entry.valuation_ccy,
                    "value": entry.valuation
                })
    return jsonify(serialize(output_entries))


@app.route(LINKED_ACCOUNT.sub_accounts(), methods=["GET"])
@jwt_required
@request_handler()
def get_linked_account_sub_accounts(user_account_id, linked_account_id):
    history_entry = repository.find_last_history_entry(db_session, user_account_id)
    if not history_entry:
        raise ApplicationError(f"No valuation available for user account '{user_account_id}'")
    linked_account_id = int(linked_account_id)
    results = repository.find_sub_accounts_valuation(db_session, history_entry.id, linked_account_id)

    return jsonify(serialize({
        "sub_accounts": [
            {
                "account": {
                    "id": entry.sub_account_id,
                    "iso_currency": entry.sub_account_ccy,
                    "description": entry.sub_account_description,
                    "type": entry.sub_account_type
                },
                "valuation": {
                    "value": entry.valuation,
                    "total_liabilities": entry.total_liabilities,
                    "value_account_ccy": entry.valuation_sub_account_ccy,
                    "change": entry.valuation_change
                }
            }
            for entry in results
        ]
    }))


REPORTS = API_V1.reports


@app.route(REPORTS.holdings(), methods=["GET"])
@jwt_required
@request_handler()
def get_holdings_report():
    user_account_id = get_jwt_identity()
    history_entry = repository.find_last_history_entry(db_session, user_account_id)
    if not history_entry:
        raise ApplicationError("No data to report")
    return jsonify(serialize({
        "report": holdings_report.generate(
            session=db_session,
            history_entry=history_entry
        )
    }))


@app.route(REPORTS.earnings(), methods=["GET"])
@jwt_required
@request_handler()
def get_earnings_report():
    user_account_id = get_jwt_identity()
    to_time = now_utc()
    return jsonify(serialize({
        "report": earnings_report.generate(
            session=db_session,
            user_account_id=user_account_id,
            from_time=to_time - timedelta(days=365),
            to_time=to_time
        )
    }))
