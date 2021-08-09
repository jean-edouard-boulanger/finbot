from finbot.core.errors import ApplicationError


class AuthenticationFailure(ApplicationError):
    def __init__(self, error_message: str):
        super().__init__(error_message, "P001")


class RetiredProviderError(ApplicationError):
    def __init__(self):
        super().__init__(f"This provider has been retired", "P002")
