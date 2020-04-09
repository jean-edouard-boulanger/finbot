from typing import Union, Dict
from finbot.apps.support import ApplicationError
from finbot.clients.finbot import FinbotClient


def validate_credentials(finbot_client: FinbotClient,
                         provider_id: int,
                         credentials: Union[Dict, None]) -> None:
    finbot_response = finbot_client.get_financial_data(
        provider=provider_id,
        credentials_data=credentials,
        line_items=[])

    if "error" in finbot_response:
        user_message = finbot_response["error"]["user_message"]
        raise ApplicationError(f"Unable to validate provided credentials ({user_message})")
