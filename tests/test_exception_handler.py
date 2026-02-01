from unittest.mock import MagicMock

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessLogicError,
    ConcurrencyError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    FileOperationError,
    NotFoundError,
    ParsingError,
    StatsBoardException,
    ValidationError,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestCreateErrorResponse:
    async def test_create_error_response_basic(self):
        from src.core.exception_handler import create_error_response

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-123"
        response = create_error_response(request, 400, "Bad Request", "TestError")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        content = bytes(response.body).decode()
        assert "test-request-123" in content

    async def test_create_error_response_without_exc_type(self):
        from src.core.exception_handler import create_error_response

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-456"
        response = create_error_response(request, 404, "Not Found")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404


class TestValidationExceptionHandler:
    async def test_validation_exception_handler(self):
        from src.core.exception_handler import validation_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-001"
        exc = ValidationError("Invalid data")

        response = await validation_exception_handler(request, exc)
        assert response.status_code == 400


class TestNotFoundExceptionHandler:
    async def test_not_found_exception_handler(self):
        from src.core.exception_handler import not_found_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-002"
        exc = NotFoundError("Resource not found")

        response = await not_found_exception_handler(request, exc)
        assert response.status_code == 404


class TestDatabaseExceptionHandler:
    async def test_database_exception_handler(self):
        from src.core.exception_handler import database_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-003"
        exc = DatabaseError("Database failed")

        response = await database_exception_handler(request, exc)
        assert response.status_code == 500


class TestBusinessLogicExceptionHandler:
    async def test_business_logic_exception_handler(self):
        from src.core.exception_handler import business_logic_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-004"
        exc = BusinessLogicError("Logic error")

        response = await business_logic_exception_handler(request, exc)
        assert response.status_code == 422


class TestStatsBoardExceptionHandler:
    async def test_statsboard_exception_handler_known_type(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-005"
        exc = AuthenticationError("Auth failed")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 401

    async def test_statsboard_exception_handler_authorization_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-006"
        exc = AuthorizationError("No permission")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 403

    async def test_statsboard_exception_handler_concurrency_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-007"
        exc = ConcurrencyError("Locked")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 409

    async def test_statsboard_exception_handler_business_logic_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-008"
        exc = BusinessLogicError("Invalid")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 422

    async def test_statsboard_exception_handler_external_service_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-009"
        exc = ExternalServiceError("Service down")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 503

    async def test_statsboard_exception_handler_configuration_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-010"
        exc = ConfigurationError("Config missing")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500

    async def test_statsboard_exception_handler_file_operation_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-011"
        exc = FileOperationError("File error")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500

    async def test_statsboard_exception_handler_parsing_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-012"
        exc = ParsingError("Parse failed")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 400

    async def test_statsboard_exception_handler_custom_exception(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-013"
        exc = StatsBoardException("Custom error")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500


class TestIntegrityErrorHandler:
    async def test_integrity_error_handler(self):
        from src.core.exception_handler import integrity_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-014"
        from sqlalchemy.exc import IntegrityError

        exc = IntegrityError("test", {}, Exception())

        response = await integrity_error_handler(request, exc)
        assert response.status_code == 409


class TestSQLAlchemyErrorHandler:
    async def test_sqlalchemy_error_handler(self):
        from src.core.exception_handler import sqlalchemy_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-015"
        from sqlalchemy.exc import SQLAlchemyError

        exc = SQLAlchemyError("DB error")

        response = await sqlalchemy_error_handler(request, exc)
        assert response.status_code == 500


class TestValueErrorHandler:
    async def test_value_error_handler(self):
        from src.core.exception_handler import value_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-016"
        exc = ValueError("Invalid value")

        response = await value_error_handler(request, exc)
        assert response.status_code == 400


class TestKeyErrorHandler:
    async def test_key_error_handler(self):
        from src.core.exception_handler import key_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-017"
        exc = KeyError("missing_key")

        response = await key_error_handler(request, exc)
        assert response.status_code == 400


class TestTypeErrorHandler:
    async def test_type_error_handler(self):
        from src.core.exception_handler import type_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-018"
        exc = TypeError("Invalid type")

        response = await type_error_handler(request, exc)
        assert response.status_code == 400


class TestConnectionErrorHandler:
    async def test_connection_error_handler(self):
        from src.core.exception_handler import connection_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-019"
        exc = ConnectionError("Cannot connect")

        response = await connection_error_handler(request, exc)
        assert response.status_code == 503


class TestTimeoutErrorHandler:
    async def test_timeout_error_handler(self):
        from src.core.exception_handler import timeout_error_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-020"
        exc = TimeoutError("Timed out")

        response = await timeout_error_handler(request, exc)
        assert response.status_code == 504


class TestGlobalExceptionHandler:
    async def test_global_exception_handler(self):
        from src.core.exception_handler import global_exception_handler

        request = MagicMock(spec=Request)
        request.state.request_id = "test-request-021"
        exc = RuntimeError("Unexpected error")

        response = await global_exception_handler(request, exc)
        assert response.status_code == 500


class TestRegisterExceptionHandlers:
    async def test_register_exception_handlers(self):
        from fastapi import FastAPI

        from src.core.exception_handler import register_exception_handlers

        app = FastAPI()
        initial_handlers = len(app.exception_handlers)

        register_exception_handlers(app)

        assert len(app.exception_handlers) > initial_handlers
