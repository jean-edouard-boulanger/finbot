from finbot.core.errors import ApplicationError


class ProviderError(ApplicationError):
    pass


class AuthenticationError(ProviderError):
    error_code = "P001"


class RetiredProviderError(ProviderError):
    error_code = "P002"

    def __init__(self) -> None:
        super().__init__("This provider has been retired")


class UnknownProvider(ProviderError):
    error_code = "P003"

    def __init__(self, provider_id: str) -> None:
        super().__init__(f"Unknown provider '{provider_id}'")


class UserConfigurationError(ProviderError):
    error_code = "P004"


class UnsupportedFinancialInstrument(ProviderError):
    error_code = "P005"

    def __init__(self, asset_type: str, asset_description: str) -> None:
        super().__init__(f"Unsupported asset type '{asset_type}': {asset_description}")


class UnsupportedAccountType(ProviderError):
    error_code = "P006"

    def __init__(self, account_type: str, account_name: str) -> None:
        super().__init__(f"Unsupported account type '{account_type}': {account_name}")
