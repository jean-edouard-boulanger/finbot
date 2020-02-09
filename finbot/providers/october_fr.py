from price_parser import Price
from selenium.webdriver.common.by import By
from finbot import providers
from finbot.providers.support.selenium import any_of, SeleniumHelper
from finbot.providers.errors import AuthFailure


AUTH_URL = "https://app.october.eu/login"
PORTFOLIO_URL = "https://app.october.eu/transactions/summary"
LOANS_URL = "https://app.october.eu/transactions/loans"


class Credentials(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def user_id(self):
        return self.username

    @staticmethod
    def init(data):
        return Credentials(data["username"], data["password"])


class Api(providers.SeleniumBased):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _go_home(self):
        self._do.get(PORTFOLIO_URL)
        return self._do.wait_element(By.CSS_SELECTOR, "div.summary")

    def authenticate(self, credentials):
        self._do.get(AUTH_URL)
        auth_area = self._do.wait_element(By.TAG_NAME, "form")
        email_input, password_input = auth_area.find_elements_by_tag_name("input")
        email_input.send_keys(credentials.username)
        password_input.send_keys(credentials.password)
        actions_area = self._do.wait_element(By.CSS_SELECTOR, "div.actions")
        actions_area.find_element_by_css_selector("button.action-button").click()

        self._do.wait_cond(any_of(
            lambda _: _get_login_error(self._do),
            lambda _: _is_logged_in(self._do)))

        error_message = _get_login_error(self._do)
        if error_message:
            raise AuthFailure(error_message)

    def get_balances(self):
        summary_area = self._go_home()
        loan_amount, cash_amount = _get_accounts_amount(summary_area)
        return {
            "accounts": [
                {
                    "account": {
                        "id": "cash",
                        "name": "Cash",
                        "iso_currency": "EUR"
                    },
                    "balance": cash_amount
                },
                {
                    "account": {
                        "id": "loan",
                        "name": "Loan",
                        "iso_currency": "EUR"
                    },
                    "balance": loan_amount,
                }
            ]
        }

    def _get_cash_assets(self):
        summary_area = self._go_home()
        _, cash_amount = _get_accounts_amount(summary_area)
        return [{
            "name": "cash",
            "type": "currency",
            "current_weight": 1.0,
            "value": cash_amount,
            "provider_specific": None
        }]

    def _get_loan_assets(self):
        def extract_loan(loan_row):
            items = loan_row.find_elements_by_tag_name("li")
            loan_name = items[0].find_element_by_css_selector("strong.project-name").text.strip()
            loan_rate = float(items[2].text.strip()[:-1]) / 100.
            loan_outstanding = Price.fromstring(items[5].text.strip())
            return {
                "name": loan_name,
                "type": "loan",
                "annual_rate": loan_rate,
                "value": loan_outstanding.amount_float,
                "provider_specific": None
            }

        self._do.get(LOANS_URL)
        table = self._do.wait_element(By.CSS_SELECTOR, "div.investment-table")
        load_button = self._do.find_maybe(By.CSS_SELECTOR, "div.load-more")
        if load_button:
            load_button.click()

        return [
            extract_loan(row)
            for row in table.find_elements_by_css_selector("ul.entry")
        ]

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": {
                        "id": account_id,
                        "name": account_id.title(),
                        "iso_currency": "EUR"
                    },
                    "assets": handler()
                }
                for account_id, handler in [
                    ("cash", self._get_cash_assets),
                    ("loan", self._get_loan_assets)
                ]
            ]
        }


def _get_login_error(browser_helper: SeleniumHelper):
    error_area = browser_helper.find_maybe(By.ID, "error-message")
    if error_area and error_area.is_displayed():
        return error_area.text.strip()


def _is_logged_in(browser_helper: SeleniumHelper):
    avatar_area = browser_helper.find_maybe(By.CSS_SELECTOR, "li.avatar")
    return avatar_area is not None


def _get_accounts_amount(summary_area):
    synthesis_area = (summary_area.find_element_by_tag_name("section")
                                  .find_element_by_tag_name("article"))
    loan_area, cash_area, *_ = synthesis_area.find_elements_by_tag_name("dl")
    loan_amount = Price.fromstring(loan_area.find_element_by_tag_name("dd").text)
    cash_amount = Price.fromstring(cash_area.find_element_by_tag_name("dd").text)
    return loan_amount.amount_float, cash_amount.amount_float
