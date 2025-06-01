from finbot.core.errors import ApplicationError


class AuthenticationFailure(ApplicationError):
    error_code = "F001"

    def __init__(self, error_message: str):
        super().__init__(error_message)
