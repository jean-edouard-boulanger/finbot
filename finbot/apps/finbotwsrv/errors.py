from finbot.core.errors import ApplicationError


class AuthenticationFailure(ApplicationError):
    def __init__(self, error_message: str):
        super().__init__(error_message, "F001")
