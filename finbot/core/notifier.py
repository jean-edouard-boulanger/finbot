from dataclasses import dataclass
from textwrap import dedent
from typing import Protocol

from twilio.rest import Client as TwilioClient


class Notifier(Protocol):
    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        ...

    def notify_twilio_settings_updated(self) -> None:
        ...


@dataclass
class TwilioSettings:
    account_sid: str
    auth_token: str
    phone_number: str

    @staticmethod
    def deserialize(data: dict[str, str]) -> "TwilioSettings":
        return TwilioSettings(
            account_sid=data["account_sid"],
            auth_token=data["auth_token"],
            phone_number=data["phone_number"],
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


class CompositeNotifier(Notifier):
    def __init__(self, notifiers: list[Notifier]):
        self.notifiers = notifiers

    def notify_valuation(
        self, valuation: float, change_1day: float | None, currency: str
    ) -> None:
        for notifier in self.notifiers:
            notifier.notify_valuation(valuation, change_1day, currency)

    def notify_twilio_settings_updated(self) -> None:
        for notifier in self.notifiers:
            notifier.notify_twilio_settings_updated()
