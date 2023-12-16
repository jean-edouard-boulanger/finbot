import smtplib
from contextlib import contextmanager
from dataclasses import dataclass
from email.header import Header as EmailHeader
from email.message import EmailMessage
from email.utils import formataddr as format_email_address
from typing import Any, Iterator, Optional, Protocol, Type, TypedDict

import jsonschema

from finbot.core.errors import FinbotError, InvalidUserInput
from finbot.core.kv_store import KVEntity

DEFAULT_SMTP_PORT = 587


class ProviderSchema(TypedDict):
    settings_schema: dict[str, Any]
    ui_schema: dict[str, Any]


GENERIC_PROVIDER_SCHEMA: ProviderSchema = {
    "settings_schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["email", "password"],
        "properties": {
            "email": {"title": "Email", "type": "string"},
            "password": {"title": "Password", "type": "string"},
        },
    },
    "ui_schema": {
        "ui:order": [
            "email",
            "password",
        ],
        "password": {"ui:widget": "password"},
    },
}


class ProviderAlreadyRegistered(FinbotError):
    def __init__(self, provider_id: str):
        super().__init__(f"email provider with id '{provider_id}' already registered")


class InvalidProviderMetadata(FinbotError):
    def __init__(self, error_message: str):
        super().__init__(error_message)


class UnknownProvider(InvalidUserInput):
    def __init__(self, provider_id: str):
        super().__init__(f"email provider with id '{provider_id}' does not exist")


class BadProviderSettings(InvalidUserInput):
    def __init__(self, error: str):
        super().__init__(f"could not validate settings: {error}")


class ProviderMetadata(TypedDict):
    provider_id: str
    description: str
    schema: ProviderSchema


class DeliverySettings(KVEntity):
    key = "Finbot.Settings.Email.Delivery"

    def __init__(
        self,
        subject_prefix: str,
        sender_name: str,
        provider_id: str,
        provider_settings: dict[str, Any],
    ):
        self.provider_id = provider_id
        self.subject_prefix = subject_prefix
        self.sender_name = sender_name
        self.provider_settings = provider_settings

    def serialize(self) -> Any:
        return {
            "subject_prefix": self.subject_prefix,
            "sender_name": self.sender_name,
            "provider_id": self.provider_id,
            "provider_settings": self.provider_settings,
        }

    @staticmethod
    def deserialize(data: Any) -> "DeliverySettings":
        return DeliverySettings(
            subject_prefix=data["subject_prefix"],
            sender_name=data["sender_name"],
            provider_id=data["provider_id"],
            provider_settings=data["provider_settings"],
        )


@dataclass(frozen=True)
class Email:
    recipients_emails: list[str]
    subject: str
    body: str


class EmailProvider(Protocol):
    provider_id: str
    description: str
    schema: ProviderSchema

    def send_email(self, message: EmailMessage) -> None:
        ...

    def get_sender_email(self) -> str:
        ...

    @staticmethod
    def create(settings_payload: DeliverySettings) -> "EmailProvider":
        ...


EMAIL_PROVIDERS: dict[str, Type[EmailProvider]] = {}


def register_provider(provider_type: Type[EmailProvider]) -> Type[EmailProvider]:
    provider_id = provider_type.provider_id
    if provider_id in EMAIL_PROVIDERS:
        raise ProviderAlreadyRegistered(provider_id)
    if "settings_schema" not in provider_type.schema:
        raise InvalidProviderMetadata(
            f"email provider '{provider_type.provider_id}'" f" is missing 'settings_schema' property"
        )
    EMAIL_PROVIDERS[provider_id] = provider_type
    return provider_type


def get_provider(settings: DeliverySettings) -> EmailProvider:
    provider_id = settings.provider_id
    if provider_id not in EMAIL_PROVIDERS:
        raise UnknownProvider(provider_id)
    provider_type = EMAIL_PROVIDERS[provider_id]
    settings_schema = provider_type.schema["settings_schema"]
    try:
        jsonschema.validate(settings.provider_settings, settings_schema)
    except jsonschema.ValidationError as e:
        raise BadProviderSettings(str(e))
    return provider_type.create(settings)


class EmailService(object):
    def __init__(self, delivery_settings: DeliverySettings):
        self._delivery_settings = delivery_settings
        self._provider = get_provider(self._delivery_settings)

    def _create_email_message(
        self,
        email: Email,
        delivery_settings: DeliverySettings,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = f"{delivery_settings.subject_prefix} {email.subject}"
        msg["From"] = format_email_address(
            (
                str(EmailHeader(delivery_settings.sender_name, "utf-8")),
                self._provider.get_sender_email(),
            )
        )
        if len(email.recipients_emails) == 1:
            msg["To"] = email.recipients_emails[0]
        else:
            msg["Bcc"] = ", ".join(email.recipients_emails)
        msg.set_content(email.body)
        return msg

    def send_email(self, email: Email) -> None:
        self._provider.send_email(
            message=self._create_email_message(
                email=email,
                delivery_settings=self._delivery_settings,
            ),
        )


def get_providers_metadata() -> list[ProviderMetadata]:
    return [
        {
            "provider_id": provider.provider_id,
            "description": provider.description,
            "schema": provider.schema,
        }
        for provider in EMAIL_PROVIDERS.values()
    ]


@contextmanager
def smtp_client(*args: Any, **kwargs: Any) -> Iterator[smtplib.SMTP]:
    server: Optional[smtplib.SMTP] = None
    try:
        server = smtplib.SMTP(*args, **kwargs)
        yield server
    finally:
        if server:
            server.quit()


class SMTPServerAuthStrategy(Protocol):
    def authenticate(self, client: smtplib.SMTP) -> None:
        ...

    @staticmethod
    def deserialize(auth_payload: dict[str, Any]) -> "SMTPServerAuthStrategy":
        ...


class SMTPServerAuthLogin(SMTPServerAuthStrategy):
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def authenticate(self, client: smtplib.SMTP) -> None:
        client.login(self._username, self._password)

    @staticmethod
    def deserialize(auth_payload: dict[str, Any]) -> "SMTPServerAuthLogin":
        return SMTPServerAuthLogin(
            username=auth_payload["username"],
            password=auth_payload["password"],
        )


class SMTPServerNoAuth(SMTPServerAuthStrategy):
    def authenticate(self, client: smtplib.SMTP) -> None:
        pass

    @staticmethod
    def deserialize(auth_payload: dict[str, Any]) -> "SMTPServerNoAuth":
        return SMTPServerNoAuth()


def get_smtp_server_auth_strategy(auth_method: str, auth_payload: dict[Any, Any]) -> SMTPServerAuthStrategy:
    methods: dict[str, type[SMTPServerAuthStrategy]] = {
        "none": SMTPServerNoAuth,
        "login": SMTPServerAuthLogin,
    }
    return methods[auth_method.lower()].deserialize(auth_payload)


@dataclass
class SMTPSenderSettings:
    smtp_server: str
    server_port: int
    use_ssl_tls: bool
    auth_strategy: SMTPServerAuthStrategy

    @staticmethod
    def deserialize(data: dict[str, Any]) -> "SMTPSenderSettings":
        return SMTPSenderSettings(
            smtp_server=data["smtp_server"],
            server_port=data["server_port"],
            use_ssl_tls=data["use_ssl_tls"],
            auth_strategy=get_smtp_server_auth_strategy(
                auth_method=data.get("auth_method", "none"),
                auth_payload=data,
            ),
        )


class SMTPSender(object):
    def __init__(self, settings: SMTPSenderSettings):
        self._settings = settings

    def send_email(self, message: EmailMessage) -> None:
        client: smtplib.SMTP
        with smtp_client(self._settings.smtp_server, self._settings.server_port) as client:
            client.ehlo()
            if self._settings.use_ssl_tls:
                client.starttls()
                client.ehlo()
            self._settings.auth_strategy.authenticate(client)
            client.send_message(message)


@register_provider
class CustomSMTPServerEmailProvider(EmailProvider):
    provider_id = "custom"
    description = "Custom SMTP server"
    schema: ProviderSchema = {
        "settings_schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": [
                "smtp_server",
                "server_port",
                "use_ssl_tls",
                "sender_email",
                "auth_method",
            ],
            "properties": {
                "smtp_server": {"title": "SMTP server", "type": "string"},
                "server_port": {
                    "title": "Server port",
                    "type": "integer",
                    "default": DEFAULT_SMTP_PORT,
                },
                "use_ssl_tls": {
                    "title": "Enable SSL/TLS",
                    "type": "boolean",
                    "default": True,
                },
                "sender_email": {
                    "title": "Sender email",
                    "type": "string",
                },
                "auth_method": {
                    "title": "Authentication method",
                    "type": "string",
                    "enum": ["None", "Login"],
                    "default": "Login",
                },
            },
            "dependencies": {
                "auth_method": {
                    "oneOf": [
                        {"properties": {"auth_method": {"enum": ["None"]}}},
                        {
                            "required": ["username", "password"],
                            "properties": {
                                "auth_method": {"enum": ["Login"]},
                                "username": {"title": "Username", "type": "string"},
                                "password": {"title": "Password", "type": "string"},
                            },
                        },
                    ]
                }
            },
        },
        "ui_schema": {
            "ui:order": [
                "smtp_server",
                "server_port",
                "use_ssl_tls",
                "sender_email",
                "auth_method",
                "username",
                "password",
            ],
            "password": {"ui:widget": "password"},
        },
    }

    def __init__(self, settings: DeliverySettings):
        self._settings = settings
        self._impl = SMTPSender(SMTPSenderSettings.deserialize(settings.provider_settings))

    def send_email(self, message: EmailMessage) -> None:
        self._impl.send_email(message)

    def get_sender_email(self) -> str:
        provider_settings = self._settings.provider_settings
        sender_email: str = provider_settings["sender_email"]
        return sender_email

    @staticmethod
    def create(settings: DeliverySettings) -> "CustomSMTPServerEmailProvider":
        return CustomSMTPServerEmailProvider(settings)


@register_provider
class OutlookProvider(EmailProvider):
    provider_id = "outlook"
    description = "Outlook / Live"
    schema: ProviderSchema = GENERIC_PROVIDER_SCHEMA

    def __init__(self, settings: DeliverySettings):
        self._settings = settings
        provider_settings = settings.provider_settings
        self._impl = SMTPSender(
            SMTPSenderSettings(
                smtp_server="smtp-mail.outlook.com",
                server_port=587,
                use_ssl_tls=True,
                auth_strategy=get_smtp_server_auth_strategy(
                    auth_method="login",
                    auth_payload={
                        "username": provider_settings["email"],
                        "password": provider_settings["password"],
                    },
                ),
            )
        )

    def send_email(self, message: EmailMessage) -> None:
        self._impl.send_email(message)

    def get_sender_email(self) -> str:
        provider_settings = self._settings.provider_settings
        sender_email: str = provider_settings["email"]
        return sender_email

    @staticmethod
    def create(settings: DeliverySettings) -> "OutlookProvider":
        return OutlookProvider(settings)
