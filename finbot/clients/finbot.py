from enum import Enum
import json
import requests


def json_dumps(data):
    return json.dumps(data, indent=4)


class LineItem(Enum):
    Balances = "balances"
    Assets = "assets"


class FinbotClient(object):
    def __init__(self, server_endpoint):
        self.server_endpoint = server_endpoint

    def get_providers(self):
        endpoint = f"{self.server_endpoint}/providers"
        return json.loads(requests.get(endpoint).content)

    def get_financial_data(self, provider, credentials_data, line_items):
        endpoint = f"{self.server_endpoint}/financial_data"
        response = requests.post(endpoint, json={
            "provider": provider,
            "credentials": credentials_data,
            "items": [item.value for item in line_items]
        })
        return json.loads(response.content)


def tester():
    finbot_client = FinbotClient("http://127.0.0.1:5000")
    print(json_dumps(finbot_client.get_providers()))
    print(json_dumps(finbot_client.get_financial_data(
        provider="vanguard_uk",
        line_items=[LineItem.Balances, LineItem.Assets],
        credentials_data={
            "username": "jboulanger2",
            "password": "***REMOVED***"
        })))


if __name__ == "__main__":
    tester()