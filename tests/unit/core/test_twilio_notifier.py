from unittest.mock import MagicMock
from typing import TypeAlias

import pytest
from twilio.rest import Client as TwilioClient

from finbot.core.notifier import TwilioNotifier, TwilioSettings, ValuationNotification


TwilioClientMock: TypeAlias = TwilioClient | MagicMock
TEST_RECIPIENT_PHONE_NUMBER = "+33687654321"
TEST_TWILIO_SETTINGS = TwilioSettings(
    account_sid="test_account_sid",
    auth_token="test_auth_token",
    phone_number="+33612345678",
)


def twilio_client_mock_factory(*_) -> TwilioClientMock:
    return MagicMock(spec_set=TwilioClient)


@pytest.fixture(scope="function")
def notifier() -> TwilioNotifier:
    return TwilioNotifier(
        twilio_settings=TEST_TWILIO_SETTINGS,
        recipient_phone_number=TEST_RECIPIENT_PHONE_NUMBER,
        twilio_client_factory=twilio_client_mock_factory,
    )


@pytest.mark.parametrize(
    "valuation_notification, expected_body",
    [
        (
            ValuationNotification(
                user_account_valuation=25_000.0,
                change_1day=None,
                valuation_currency="EUR",
            ),
            "💰 Finbot valuation: 25,000.0 EUR\n",
        ),
        (
            ValuationNotification(
                user_account_valuation=1000.0,
                change_1day=100.0,
                valuation_currency="EUR",
            ),
            "💰 Finbot valuation: 1,000.0 EUR\n1 day change: 100.0 EUR ⬆️\n",
        ),
        (
            ValuationNotification(
                user_account_valuation=500.0,
                change_1day=-50.0,
                valuation_currency="GBP",
            ),
            "💰 Finbot valuation: 500.0 GBP\n1 day change: -50.0 GBP ⬇️\n",
        ),
    ],
)
def test_notify_valuation(
    notifier: TwilioNotifier,
    valuation_notification: ValuationNotification,
    expected_body: str,
):
    notifier.notify_valuation(notification=valuation_notification)
    notifier._twilio_client.messages.create.assert_called_once_with(
        to=TEST_RECIPIENT_PHONE_NUMBER,
        from_=TEST_TWILIO_SETTINGS.phone_number,
        body=expected_body,
    )


def test_notify_twilio_settings_updated(notifier: TwilioNotifier):
    notifier.notify_twilio_settings_updated()
    notifier._twilio_client.messages.create.assert_called_once_with(
        to=TEST_RECIPIENT_PHONE_NUMBER,
        from_=TEST_TWILIO_SETTINGS.phone_number,
        body="☎️ Your Twilio integration settings have been successfully updated",
    )


def test_notify_linked_accounts_snapshot_errors(notifier: TwilioNotifier):
    notifier._twilio_client.messages.create.assert_not_called()
