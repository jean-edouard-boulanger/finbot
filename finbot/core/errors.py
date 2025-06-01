class FinbotError(Exception):
    """Base class for all Finbot errors"""

    def __init__(self, error_message: str) -> None:
        super().__init__(error_message)


class ApplicationError(FinbotError):
    error_code: str = "G00X"

    def __init__(self, error_message: str) -> None:
        super().__init__(error_message)


class InvalidUserInput(ApplicationError):
    error_code = "G001"


class InvalidOperation(ApplicationError):
    error_code = "G002"


class MissingUserData(ApplicationError):
    error_code = "G003"


class NotAllowedError(ApplicationError):
    error_code = "G004"

    def __init__(self, error_message: str = "Not allowed"):
        super().__init__(error_message)


class ResourceNotFoundError(ApplicationError):
    error_code = "G005"


class AuthError(ApplicationError):
    error_code = "A00X"


class InvalidJwtError(AuthError):
    error_code = "A001"

    def __init__(self) -> None:
        super().__init__("Invalid JWT token")
