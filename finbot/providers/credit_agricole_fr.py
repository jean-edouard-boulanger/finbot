from copy import deepcopy
from price_parser import Price
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.common.exceptions import StaleElementReferenceException
from finbot.providers.support.selenium import (
    any_of, 
    all_of, 
    negate
)
from finbot import providers
from finbot.core.utils import swallow_exc
from finbot.providers.errors import AuthFailure
import time
import json


AUTH_URL = "https://www.credit-agricole.fr/{region}/particulier/acceder-a-mes-comptes.html"


class Credentials(object):
    def __init__(self, region, account_number, password):
        self.region = region
        self.account_number = account_number
        self.password = password

    @property
    def user_id(self):
        return self.account_number

    @staticmethod
    def init(data):
        return Credentials(data["region"], data["account_number"], data["password"])


@swallow_exc(StaleElementReferenceException)
def _get_login_error(browser_helper: providers.SeleniumHelper):
    error_items = [
        item for item in browser_helper.find_many(
            By.CSS_SELECTOR, "div.error")
        if item.is_displayed()
    ]
    if error_items:
        return error_items[0].text


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_data = None

    def _iter_accounts(self):
        def handle_account(data):
            return {
                "account": {
                    "id": data["numeroCompte"].strip(),
                    "name": data["libelleUsuelProduit"].strip(),
                    "iso_currency": data["idDevise"].strip()
                },
                "balance": data["solde"]
            }
        yield handle_account(self.account_data["comptePrincipal"])
        for line_item in self.account_data["grandesFamilles"]:
            for account_data in line_item["elementsContrats"]:
                yield handle_account(account_data)

    def authenticate(self, credentials):
        self._do.get(AUTH_URL.format(region=credentials.region))

        # 1. Enter account number

        account_input = self._do.wait_element(By.ID, "Login-account")
        account_input.send_keys(credentials.account_number)
        self._do.find(By.XPATH, "//button[@login-submit-btn]").click()

        # 2. Type password and validate

        login_keys_by_num = {}
        login_keys = self._do.find_many(By.CLASS_NAME, "Login-key")
        for key in login_keys:
            self._do.wait_cond(lambda _: len(key.text) > 0)
            login_keys_by_num[key.text.strip()] = key
        for digit in credentials.password:
            login_keys_by_num[digit].click()
        self._do.find(By.ID, "validation").click()

        # 3. Wait logged-in or error

        self._do.wait_cond(any_of(
            lambda _: _get_error(self._do),
            lambda _: self._do.find_maybe(By.CLASS_NAME, "Synthesis-user")))

        error_message = _get_login_error(self._do)
        if error_message:
            raise AuthFailure(error_message)

        # 4. Extract accounts data

        controller = self._do.wait_element(By.XPATH, "//div[@data-ng-controller]")
        account_data_str = controller.get_attribute("data-ng-init")[len("syntheseController.init("):-1]
        self.account_data = json.loads("[" + account_data_str + "]")[0]

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "balance": entry["balance"]
                }
                for entry in self._iter_accounts()
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "assets": [{
                        "name": "cash",
                        "type": "currency",
                        "value": entry["balance"]
                    }]
                }
                for entry in self._iter_accounts()
            ]
        }