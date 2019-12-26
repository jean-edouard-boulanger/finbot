#!/usr/bin/env python3.7
from functools import partial
from contextlib import closing
from multiprocessing.pool import ThreadPool
from finbot.providers.support.selenium import DefaultBrowserFactory
from finbot.apps.core import get_provider
from finbot.core import crypto, fx
import functools
import traceback
import argparse
import logging
import sys
import json
import terminaltables
import time


def json_dumps(data):
    return json.dumps(data, indent=4)


@functools.lru_cache(128)
def get_fx_rate(home_ccy, foreign_ccy):
    return fx.get_xccy_rate(home_ccy, foreign_ccy)


def wait_forever():
    while True:
        time.sleep(60)


class Price(object):
    def __init__(self, amount, currency):
        self._amount = amount
        self._currency = currency

    def amount(self, currency_override=None):
        if currency_override is not None:
            return self._amount * get_fx_rate(self._currency, currency_override)
        return self._amount

    def currency(self):
        return self._currency


class Asset(object):
    def __init__(self, name, amount):
        self.name = name
        self._amount = amount

    def amount(self, currency_override=None):
        return self._amount.amount(currency_override)


class ProviderData(object):
    def __init__(self, name, accounts=None):
        self.name = name
        self.accounts = accounts or {}

    def amount(self, currency):
        return sum(account.amount(currency) for account in self.accounts.values())


class AccountData(object):
    def __init__(self, account=None, balance=None, assets=None):
        self.account = account
        self.balance = balance
        self.assets = assets or []

    def amount(self, currency_override=None):
        return self.balance.amount(currency_override)


class AssetTree(object):
    def __init__(self, providers=None):
        self.providers = providers or []

    def amount(self, currency):
        return sum(provider.amount(currency) for provider in self.providers)


def fetch_balances(settings, browser_factory, account):
    provider = get_provider(account["provider_id"])
    with closing(provider.api_module.Api(browser_factory)) as api:
        try:
            credentials = provider.api_module.Credentials.init(account["credentials"])
            logging.info(f"[{provider.description}] authenticate {credentials.user_id}")
            api.authenticate(credentials)
            logging.info(f"[{provider.description}] authenticate - done")

            provider_data = ProviderData(name=provider.description)

            logging.info(f"[{provider.description}] fetching balances")
            balances = api.get_balances()
            if settings.dump_balances:
                logging.info(f"[{provider.description}] balances {json_dumps(balances)}")
            for entry in balances["accounts"]:
                account = entry["account"]
                account_data = AccountData(
                    account=account,
                    balance=Price(entry["balance"], account["iso_currency"]))
                provider_data.accounts[account["id"]] = account_data
            logging.info(f"[{provider.description}] fetching balances - done")

            logging.info(f"[{provider.description}] fetching assets")
            assets = api.get_assets()
            if settings.dump_assets:
                logging.info(f"[{provider.description}] assets {json_dumps(assets)}")
            for entry in assets["accounts"]:
                account = entry["account"]
                account_data = provider_data.accounts[account["id"]]
                for asset in entry["assets"]:
                    account_data.assets.append(Asset(
                        name=asset["name"],
                        amount=Price(asset["value"], account["iso_currency"])
                    ))
            logging.info(f"[{provider.description}] fetching assets - done")
            return provider_data
        except KeyboardInterrupt:
            raise
        except Exception:
            if settings.pause_on_error:
                logging.warning(traceback.format_exc())
                logging.warning("PAUSING execution because of error")
                logging.warning("CTRL^C to exit")
                wait_forever()
            raise


def flatten_accounts_list(accounts_str_list):
    all_accounts = []
    for accounts in accounts_str_list:
        all_accounts += accounts
    return all_accounts


def create_arguments_parser():
    parser = argparse.ArgumentParser("finance automation tester")
    parser.add_argument("accounts", metavar="accounts", type=lambda s: s.split(","), nargs="*")
    parser.add_argument("--secret-file", required=True)
    parser.add_argument("--dump-balances", action="store_true", default=False)
    parser.add_argument("--dump-assets", action="store_true", default=False)
    parser.add_argument("--accounts-file", required=True)
    parser.add_argument("--show-browser", action="store_false", default=True, dest="headless")
    parser.add_argument("--no-threadpool", action="store_false", default=True, dest="threadpool")
    parser.add_argument("--pause-on-error", action="store_true", default=False, dest="pause_on_error")
    parser.add_argument("--currency", type=str, default="GBP")
    return parser


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)')
    parser = create_arguments_parser()
    settings = parser.parse_args()
    browser_factory = DefaultBrowserFactory(headless=settings.headless)
    selected_providers = flatten_accounts_list(settings.accounts)
    load_all = all(provider_id.startswith("~") for provider_id in selected_providers)

    with open(settings.secret_file, "rb") as secret_file:
        secret = secret_file.read()
        with open(settings.accounts_file, "rb") as accounts_file:
            all_accounts = json.loads(
                crypto.fernet_decrypt(accounts_file.read(), secret).decode())["accounts"]

    logging.info(f"selected accounts: {', '.join(selected_providers)}")

    selected_accounts = [
        account for account in all_accounts
        if (load_all and f"~{account['provider_id']}" not in selected_providers)
        or (account["provider_id"] in selected_providers)
    ]

    try:
        fetcher = partial(fetch_balances, settings, browser_factory)
        if settings.threadpool:
            with ThreadPool(processes=8) as pool:
                all_data = pool.map(fetcher, selected_accounts)
        else:
            all_data = map(fetcher, selected_accounts)

        asset_tree = AssetTree(all_data)
        all_assets_amount = asset_tree.amount(settings.currency)
        if all_assets_amount == 0.0:
            print("no assets")
            return

        raw_table = [["Account", "Amount", "Weight", "Currency"]]
        raw_table.append([
            "(All assets)",
            f"{all_assets_amount:.2f}",
            "100.00%",
            settings.currency])
        raw_table.append(["", "", ""])
        for provider_data in asset_tree.providers:
            provider_amount = provider_data.amount(settings.currency)
            provider_pc = (provider_amount / all_assets_amount) * 100.0
            raw_table.append([
                f"  + {provider_data.name}",
                f"{provider_amount:.2f}",
                f"{provider_pc:.2f}%",
                settings.currency])
            for account_data in provider_data.accounts.values():
                account_amount = account_data.amount(settings.currency)
                account_pc = (account_amount / all_assets_amount) * 100.0
                raw_table.append([
                    f"    + {account_data.account['name']} ",
                    f"{account_amount:.2f}",
                    f"{account_pc:.2f}%",
                    settings.currency
                ])
                for asset in account_data.assets:
                    asset_amount = asset.amount(settings.currency)
                    asset_pc = (asset_amount / all_assets_amount) * 100.0
                    raw_table.append([
                        f"      * {asset.name.title()}",
                        f"{asset_amount:.2f}",
                        f"{asset_pc:.2f}%",
                        settings.currency
                    ])
            raw_table.append(["", "", ""])

        print(terminaltables.AsciiTable(raw_table).table)

    except Exception:
        logging.fatal(traceback.format_exc())


if __name__ == "__main__":
    main()
