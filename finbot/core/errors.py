class FinbotError(Exception):
    """Base class for all Finbot errors"""

    def __init__(self, error_message: str) -> None:
        super().__init__(error_message)


class ApplicationError(FinbotError):
    def __init__(self, error_message: str, error_code: str) -> None:
        super().__init__(error_message)
        self.error_code = error_code


class InvalidUserInput(ApplicationError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message, "G001")


class InvalidOperation(ApplicationError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message, "G002")


class MissingUserData(ApplicationError):
    def __init__(self, error_message: str) -> None:
        super().__init__(error_message, "G003")
