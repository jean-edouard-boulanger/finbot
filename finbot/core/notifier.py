from textwrap import dedent
from typing import Callable, Protocol

from twilio.rest import Client as TwilioClient

from finbot import model
from finbot.core import email_delivery
from finbot.core.environment import TwilioEnvironment
from finbot.core.schema import BaseModel


class TwilioSettings(BaseModel):
    account_sid: str
    auth_token: str
    sender_name: str

    @staticmethod
    def from_env(twilio_env: TwilioEnvironment) -> "TwilioSettings":
        return TwilioSettings(
            account_sid=twilio_env.account_sid,
            auth_token=twilio_env.auth_token,
            sender_name=twilio_env.sender_name,
        )


class ValuationNotification(BaseModel):
    user_account_valuation: float
    change_1day: float | None
    valuation_currency: str


class Notifier(Protocol):
    def notify_valuation(
        self,
        notification: ValuationNotification,
    ) -> None: ...

    def notify_linked_accounts_snapshot_errors(
        self,
        error_entries: list[model.LinkedAccountSnapshotEntry],
    ) -> None: ...


class EmailNotifier(Notifier):
    def __init__(
        self,
        email_delivery_settings: email_delivery.DeliverySettings,
        recipient_email: str,
    ):
        self._email_delivery_settings = email_delivery_settings
        self._recipient_email = recipient_email
        self._service = email_delivery.EmailService(email_delivery_settings)

    def notify_valuation(self, notification: ValuationNotification) -> None:
        pass

    def notify_linked_accounts_snapshot_errors(
        self,
        error_entries: list[model.LinkedAccountSnapshotEntry],
    ) -> None:
        self._service.send_email(
            email=email_delivery.Email(
                recipients_emails=[self._recipient_email],
                subject=f"There is an issue with {len(error_entries)} of your linked account(s)",
                body=dedent(
                    f"""\
                Finbot failed to get a snapshot from the following linked accounts: \
                {(", ".join(entry.linked_account.account_name for entry in error_entries)).strip()}
                """
                ),
            )
        )


def _default_twilio_client_factory(settings: TwilioSettings) -> TwilioClient:
    return TwilioClient(settings.account_sid, settings.auth_token)


class TwilioNotifier(Notifier):
    def __init__(
        self,
        twilio_settings: TwilioSettings,
        recipient_phone_number: str,
        twilio_client_factory: Callable[[TwilioSettings], TwilioClient] | None = None,
    ):
        twilio_client_factory = twilio_client_factory or _default_twilio_client_factory
        self._settings = twilio_settings
        self._recipient_phone_number = recipient_phone_number
        self._twilio_client = twilio_client_factory(self._settings)

    def notify_valuation(
        self,
        notification: ValuationNotification,
    ) -> None:
        message_body = (
            f"💰 Finbot valuation: {notification.user_account_valuation:,.1f} {notification.valuation_currency}\n"
        )
        if notification.change_1day is not None:
            message_body += (
                f"1 day change: {notification.change_1day:,.1f} {notification.valuation_currency}"
                f" {'⬆️' if notification.change_1day >= 0 else '⬇️'}\n"
            )
        self._twilio_client.messages.create(
            to=self._recipient_phone_number,
            from_=self._settings.sender_name,
            body=message_body,
        )

    def notify_linked_accounts_snapshot_errors(
        self,
        error_entries: list[model.LinkedAccountSnapshotEntry],
    ) -> None:
        pass


class CompositeNotifier(Notifier):
    def __init__(self, notifiers: list[Notifier]):
        self._notifiers = notifiers

    def notify_valuation(self, notification: ValuationNotification) -> None:
        for notifier in self._notifiers:
            notifier.notify_valuation(notification)

    def notify_linked_accounts_snapshot_errors(
        self,
        error_entries: list[model.LinkedAccountSnapshotEntry],
    ) -> None:
        for notifier in self._notifiers:
            notifier.notify_linked_accounts_snapshot_errors(error_entries)
