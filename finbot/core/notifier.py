from textwrap import dedent
from typing import Protocol

from pydantic import BaseModel
from twilio.rest import Client as TwilioClient

from finbot import model
from finbot.core import email_delivery


class Notifier(Protocol):
    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        ...

    def notify_twilio_settings_updated(self) -> None:
        ...

    def notify_linked_accounts_snapshot_errors(
        self, error_entries: list[model.LinkedAccountSnapshotEntry]
    ) -> None:
        ...


class TwilioSettings(BaseModel):
    account_sid: str
    auth_token: str
    phone_number: str


class EmailNotifier(Notifier):
    def __init__(
        self,
        email_delivery_settings: email_delivery.DeliverySettings,
        recipient_email: str,
    ):
        self._email_delivery_settings = email_delivery_settings
        self._recipient_email = recipient_email
        self._service = email_delivery.EmailService(email_delivery_settings)

    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        pass

    def notify_twilio_settings_updated(self) -> None:
        pass

    def notify_linked_accounts_snapshot_errors(
        self, error_entries: list[model.LinkedAccountSnapshotEntry]
    ) -> None:
        self._service.send_email(
            email=email_delivery.Email(
                recipients_emails=[self._recipient_email],
                subject=f"There is an issue with {len(error_entries)} of your linked account(s)",
                body=dedent(
                    f"""\
                Finbot failed to get a snapshot from the following linked accounts: \
                {(', '.join(entry.linked_account.account_name for entry in error_entries)).strip()}
                """
                ),
            )
        )


class TwilioNotifier(Notifier):
    def __init__(self, twilio_settings: TwilioSettings, recipient_phone_number: str):
        self._settings = twilio_settings
        self._recipient_phone_number = recipient_phone_number
        self._client = TwilioClient(
            self._settings.account_sid, self._settings.auth_token
        )

    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        message_body = f"💰 Finbot valuation: {valuation:,.1f} {currency}\n"
        if change_1day is not None:
            message_body += f"1 day change: {change_1day:,.1f} {currency} {'⬆️' if change_1day >= 0 else '⬇️'}\n"
        self._client.messages.create(
            to=self._recipient_phone_number,
            from_=self._settings.phone_number,
            body=message_body,
        )

    def notify_twilio_settings_updated(self) -> None:
        self._client.messages.create(
            to=self._recipient_phone_number,
            from_=self._settings.phone_number,
            body=dedent(
                """\
                ☎️ Your Twilio integration settings have been successfully updated
            """
            ).strip(),
        )

    def notify_linked_accounts_snapshot_errors(
        self, error_entries: list[model.LinkedAccountSnapshotEntry]
    ) -> None:
        pass


class CompositeNotifier(Notifier):
    def __init__(self, notifiers: list[Notifier]):
        self._notifiers = notifiers

    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        for notifier in self._notifiers:
            notifier.notify_valuation(valuation, change_1day, currency)

    def notify_twilio_settings_updated(self) -> None:
        for notifier in self._notifiers:
            notifier.notify_twilio_settings_updated()

    def notify_linked_accounts_snapshot_errors(
        self, error_entries: list[model.LinkedAccountSnapshotEntry]
    ) -> None:
        for notifier in self._notifiers:
            notifier.notify_linked_accounts_snapshot_errors(error_entries)
