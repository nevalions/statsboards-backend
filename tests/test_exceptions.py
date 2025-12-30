import pytest

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConfigurationError,
    ConcurrencyError,
    DatabaseError,
    ExternalServiceError,
    FileOperationError,
    NotFoundError,
    ParsingError,
    StatsBoardException,
    ValidationError,
)


class TestStatsBoardException:
    def test_base_exception_creation(self):
        exc = StatsBoardException("Test error")
        assert exc.message == "Test error"
        assert exc.details == {}
        assert str(exc) == "Test error"

    def test_base_exception_with_details(self):
        details = {"field": "test", "value": 123}
        exc = StatsBoardException("Test error", details)
        assert exc.message == "Test error"
        assert exc.details == details

    def test_database_error(self):
        exc = DatabaseError("DB connection failed")
        assert isinstance(exc, StatsBoardException)
        assert "DatabaseError" in str(type(exc))
        assert exc.message == "DB connection failed"

    def test_validation_error(self):
        exc = ValidationError("Invalid email format")
        assert isinstance(exc, StatsBoardException)
        assert exc.message == "Invalid email format"

    def test_not_found_error(self):
        exc = NotFoundError("Team not found", {"team_id": 123})
        assert exc.message == "Team not found"
        assert exc.details == {"team_id": 123}

    def test_business_logic_error(self):
        exc = BusinessLogicError("Cannot delete team with active matches")
        assert isinstance(exc, StatsBoardException)

    def test_external_service_error(self):
        exc = ExternalServiceError("EESL service unavailable")
        assert isinstance(exc, StatsBoardException)

    def test_configuration_error(self):
        exc = ConfigurationError("Missing DATABASE_URL")
        assert isinstance(exc, StatsBoardException)

    def test_authentication_error(self):
        exc = AuthenticationError("Invalid credentials")
        assert isinstance(exc, StatsBoardException)

    def test_authorization_error(self):
        exc = AuthorizationError("Insufficient permissions")
        assert isinstance(exc, StatsBoardException)

    def test_concurrency_error(self):
        exc = ConcurrencyError("Resource locked by another transaction")
        assert isinstance(exc, StatsBoardException)

    def test_file_operation_error(self):
        exc = FileOperationError("Failed to upload file")
        assert isinstance(exc, StatsBoardException)

    def test_parsing_error(self):
        exc = ParsingError("Invalid JSON structure")
        assert isinstance(exc, StatsBoardException)

    def test_exception_inheritance_chain(self):
        exc = ValidationError("test")
        assert isinstance(exc, StatsBoardException)
        assert isinstance(exc, Exception)


class TestExceptionDetails:
    def test_multiple_details(self):
        details = {"field1": "value1", "field2": "value2", "nested": {"key": "value"}}
        exc = StatsBoardException("Error with details", details)
        assert exc.details == details

    def test_empty_details(self):
        exc = StatsBoardException("Error", {})
        assert exc.details == {}

    def test_none_details_default(self):
        exc = StatsBoardException("Error", None)
        assert exc.details == {}
