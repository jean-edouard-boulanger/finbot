from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    jwt_required,
)
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload, contains_eager
from sqlalchemy.exc import IntegrityError
from finbot.clients.finbot import FinbotClient
from finbot.apps.appwsrv import timeseries
from finbot.apps.support import request_handler, Route, ApplicationError
from finbot.core.utils import serialize
from finbot.core import crypto
from finbot.core import dbutils
from finbot.model import (
    Provider,
    UserAccount,
    UserAccountSettings,
    LinkedAccount,
    UserAccountHistoryEntry,
    LinkedAccountValuationHistoryEntry,
)
import logging.config
import logging
import json
import os


#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


SECRET = open(os.environ["FINBOT_SECRET_PATH"], "r").read()
FINBOT_FINBOTWSRV_ENDPOINT = os.environ["FINBOT_FINBOTWSRV_ENDPOINT"]


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


AUTH = API_V1.auth


@app.route(AUTH.login._, methods=["POST"])
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
        raise ApplicationError("invalid email or password")
    
    # TODO: password should be hashed, not encrypted/decrypted with secret
    account_password = crypto.fernet_decrypt(
        account.encrypted_password.encode(), SECRET.encode()).decode()
    if account_password != data["password"]:
        raise ApplicationError("invalid email or password")

    return jsonify({
        "auth": {
            "access_token": create_access_token(identity=account.id),
            "refresh_token": create_refresh_token(identity=account.id),
        },
        "account": {
            "id": account.id,
            "email": account.email,
            "full_name": account.full_name,
            "created_at": account.created_at,
            "updated_at": account.updated_at
        }
    })


@app.route(AUTH.valid._, methods=["GET"])
@request_handler()
@jwt_required
def test_auth_validity():
    return jsonify({})


@app.route(API_V1.providers._, methods=["POST"])
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
def create_provider():
    data = request.json
    with db_session.persist(Provider()) as provider:
        provider.id = data["id"]
        provider.description = data["description"]
        provider.website_url = data["website_url"]
        provider.credentials_schema = data["credentials_schema"]
    return jsonify(provider.serialize())


@app.route(API_V1.providers._, methods=["GET"])
@request_handler()
def get_providers():
    providers = db_session.query(Provider).all()
    return jsonify(serialize({
        "providers": [provider for provider in providers]
    }))


@app.route(API_V1.providers.p("provider_id")._, methods=["DELETE"])
@request_handler()
def delete_provider(provider_id):
    count = db_session.query(Provider).filter_by(id=provider_id).delete()
    db_session.commit()
    logging.info(f"deleted provider_id={provider_id}")
    return jsonify({"deleted": count})


ACCOUNTS = API_V1.accounts


@app.route(ACCOUNTS._, methods=["POST"])
@request_handler(schema={
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
            user_account.encrypted_password = crypto.fernet_encrypt(
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


@app.route(ACCOUNT._, methods=["GET"])
@request_handler()
def get_user_account(user_account_id):
    def serialize_valuation(entry):
        return {
            "history_entry_id": entry.id,
            "date": entry.effective_at,
            "currency": entry.valuation_ccy,
            "value": entry.user_account_valuation_history_entry.valuation,
            "total_liabilities": entry.user_account_valuation_history_entry.total_liabilities,
            "change": entry.user_account_valuation_history_entry.valuation_change
        }

    account = (db_session.query(UserAccount)
                         .filter_by(id=user_account_id)
                         .options(joinedload(UserAccount.settings))
                         .first())

    if not account:
        raise ApplicationError(f"user account '{user_account_id}' not found")

    valuation = (db_session.query(UserAccountHistoryEntry)
                           .filter_by(user_account_id=user_account_id)
                           .filter_by(available=True)
                           .order_by(desc(UserAccountHistoryEntry.effective_at))
                           .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry))
                           .first())

    return jsonify(serialize({
        "result": {
            "user_account": {
                "id": account.id,
                "email": account.email,
                "full_name": account.full_name,
                "settings": {
                    "valuation_ccy": account.settings.valuation_ccy,
                    "created_at": account.settings.created_at,
                    "updated_at": account.settings.updated_at
                },
                "created_at": account.created_at,
                "updated_at": account.updated_at
            },
            "valuation": serialize_valuation(valuation) if valuation else None
        }
    }))


@app.route(ACCOUNT.history._, methods=["GET"])
@request_handler()
def get_user_account_valuation_history(user_account_id):
    history_entries = (db_session.query(UserAccountHistoryEntry)
                                 .filter_by(user_account_id=user_account_id)
                                 .filter_by(available=True)
                                 .order_by(asc(UserAccountHistoryEntry.effective_at))
                                 .options(joinedload(UserAccountHistoryEntry.user_account_valuation_history_entry, innerjoin=True))
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
                    frequency=timedelta(days=1))
        ]
    }))


@app.route(ACCOUNT.linked_accounts._, methods=["GET"])
@request_handler()
def get_linked_accounts_valuation(user_account_id):
    result = (db_session.query(UserAccountHistoryEntry)
                        .filter_by(user_account_id=user_account_id)
                        .filter_by(available=True)
                        .order_by(desc(UserAccountHistoryEntry.effective_at))
                        .options(joinedload(UserAccountHistoryEntry.linked_accounts_valuation_history_entries))
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.valuation_change)
                        )
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.linked_account)
                        )
                        .options(
                            joinedload(
                                UserAccountHistoryEntry.linked_accounts_valuation_history_entries,
                                LinkedAccountValuationHistoryEntry.effective_snapshot)
                        )
                        .first())

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
                                else result.effective_at),
                    "currency": result.valuation_ccy,
                    "value": entry.valuation,
                    "change": entry.valuation_change
                }
            }
            for entry in (result.linked_accounts_valuation_history_entries
                          if result else [])
        ]
    }))


@app.route(ACCOUNT.linked_accounts._, methods=["POST"])
@request_handler(schema={
    "type": "object",
    "additionalProperties": False,
    "required": ["provider_id", "credentials", "account_name"],
    "properties": {
        "provider_id": {"type": "string"},
        "credentials": {"type": ["null", "object"]},
        "account_name": {"type": "string"}
    }
})
def link_to_external_account(user_account_id):
    do_validate = bool(int(request.args.get("validate", 1)))
    do_persist = bool(int(request.args.get("persist", 1)))
    request_data = request.json

    logging.info(f"validate={do_validate} persist={do_persist}")

    user_account = (db_session.query(UserAccount)
                              .filter_by(id=user_account_id)
                              .first())

    if not user_account:
        raise ApplicationError(f"could not find user account with id '{user_account_id}'")

    provider_id = request_data["provider_id"]
    provider = (db_session.query(Provider)
                          .filter_by(id=provider_id)
                          .first())

    if not provider:
        raise ApplicationError(f"could not find provider with id '{provider_id}'")

    if do_validate:
        logging.info(f"validating authentication details for "
                     f"account_id={user_account_id} and provider_id={provider_id}")

        finbot_client = FinbotClient(FINBOT_FINBOTWSRV_ENDPOINT)
        finbot_response = finbot_client.get_financial_data(
            provider=provider_id,
            credentials_data=request_data["credentials"],
            line_items=[])

        if "error" in finbot_response:
            user_message = finbot_response["error"]["user_message"]
            raise ApplicationError(f"Unable to validate provided credentials ({user_message})")

    if do_persist:
        logging.info(f"Linking external account (provider_id={provider.id}) to user account_id={user_account.id}")
        try:
            with db_session.persist(user_account):
                encrypted_credentials = crypto.fernet_encrypt(
                    json.dumps(request_data["credentials"]).encode(), SECRET).decode()
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


@app.route(LINKED_ACCOUNT.history._, methods=["GET"])
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
