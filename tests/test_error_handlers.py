import importlib

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.error_handlers import DatabaseErrorHandler, sanitize_error_message


class TestSanitizeErrorMessage:
    def test_returns_full_error_in_debug_mode(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "true")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        error = Exception("Detailed error message")
        result = sanitize_error_message(error, "Generic message")
        assert result == "Detailed error message"

    def test_returns_generic_message_in_production_mode(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        error = Exception("Detailed error message")
        result = sanitize_error_message(error, "Generic message")
        assert result == "Generic message"

    def test_default_generic_message(self, monkeypatch):
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        error = Exception("Detailed error message")
        result = sanitize_error_message(error)
        assert result == "Internal server error"


class TestDatabaseErrorHandler:
    @pytest.fixture
    def mock_logger(self):
        from unittest.mock import MagicMock

        return MagicMock()

    @pytest.fixture
    def handler(self, mock_logger):
        return DatabaseErrorHandler("TestModel", mock_logger)

    def test_handle_not_found_raises_404(self, handler):
        with pytest.raises(HTTPException) as exc_info:
            handler.handle_not_found(123)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resource not found"

    def test_handle_not_found_with_custom_field_name(self, handler):
        with pytest.raises(HTTPException) as exc_info:
            handler.handle_not_found("test-123", field_name="slug")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Resource not found"

    def test_handle_conflict_raises_409(self, handler):
        with pytest.raises(HTTPException) as exc_info:
            handler.handle_conflict()
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Conflict creating TestModel"

    def test_handle_conflict_with_custom_detail(self, handler):
        custom_detail = "Custom conflict message"
        with pytest.raises(HTTPException) as exc_info:
            handler.handle_conflict(detail=custom_detail)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == custom_detail

    def test_handle_db_error_integrity_error(self, handler, mock_logger):
        error = IntegrityError("test", {}, Exception())

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        with pytest.raises(HTTPException) as exc_info:
            handler.handle_db_error(error, "test context")

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Resource already exists or violates constraints"
        mock_logger.error.assert_called_once()

    def test_handle_db_error_sqlalchemy_error(self, handler, mock_logger):
        error = SQLAlchemyError("Database error")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        with pytest.raises(HTTPException) as exc_info:
            handler.handle_db_error(error, "test context")

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Database operation failed"
        mock_logger.error.assert_called_once()

    def test_handle_db_error_generic_exception(self, handler, mock_logger):
        error = Exception("Generic error")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        with pytest.raises(HTTPException) as exc_info:
            handler.handle_db_error(error, "test context")

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal server error"
        mock_logger.error.assert_called_once()

    def test_handle_db_error_with_empty_context(self, handler, mock_logger):
        error = SQLAlchemyError("Database error")

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("DEBUG", "false")
        import src.core.error_handlers as eh

        importlib.reload(eh)

        with pytest.raises(HTTPException):
            handler.handle_db_error(error)

        mock_logger.error.assert_called_once()
