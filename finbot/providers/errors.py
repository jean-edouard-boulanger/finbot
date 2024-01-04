from finbot.core.errors import ApplicationError


class ProviderError(ApplicationError):
    def __init__(self, error_message: str, error_code: str):
        super().__init__(error_message, error_code)


class AuthenticationError(ProviderError):
    def __init__(self, error_message: str):
        super().__init__(error_message, "P001")


class RetiredProviderError(ProviderError):
    def __init__(self) -> None:
        super().__init__("This provider has been retired", "P002")


class UnknownProvider(ProviderError):
    def __init__(self, provider_id: str) -> None:
        super().__init__(f"Unknown provider '{provider_id}'", "P003")


class UserConfigurationError(ProviderError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message, "P004")


class UnsupportedFinancialInstrument(ProviderError):
    def __init__(self, asset_type: str, asset_description) -> None:
        super().__init__(f"Unsupported asset type '{asset_type}': {asset_description}", "P005")
