from typing import Any


class StatsBoardException(Exception):
    """Base exception for all application-specific errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(StatsBoardException):
    """Database-related errors"""

    pass


class ValidationError(StatsBoardException):
    """Data validation errors"""

    pass


class NotFoundError(StatsBoardException):
    """Resource not found errors"""

    pass


class BusinessLogicError(StatsBoardException):
    """Business rule violations"""

    pass


class ExternalServiceError(StatsBoardException):
    """External service integration errors"""

    pass


class ConfigurationError(StatsBoardException):
    """Configuration-related errors"""

    pass


class AuthenticationError(StatsBoardException):
    """Authentication-related errors"""

    pass


class AuthorizationError(StatsBoardException):
    """Authorization-related errors"""

    pass


class ConcurrencyError(StatsBoardException):
    """Concurrency and race condition errors"""

    pass


class FileOperationError(StatsBoardException):
    """File upload/download operation errors"""

    pass


class ParsingError(StatsBoardException):
    """Data parsing errors"""

    pass
