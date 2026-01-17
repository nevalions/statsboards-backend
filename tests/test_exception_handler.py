from unittest.mock import MagicMock

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


class TestCreateErrorResponse:
    def test_create_error_response_basic(self):
        from src.core.exception_handler import create_error_response

        response = create_error_response(400, "Bad Request", "TestError")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_create_error_response_without_exc_type(self):
        from src.core.exception_handler import create_error_response

        response = create_error_response(404, "Not Found")
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404


class TestValidationExceptionHandler:
    async def test_validation_exception_handler(self):
        from src.core.exception_handler import validation_exception_handler

        request = MagicMock(spec=Request)
        exc = ValidationError("Invalid data")

        response = await validation_exception_handler(request, exc)
        assert response.status_code == 400


class TestNotFoundExceptionHandler:
    async def test_not_found_exception_handler(self):
        from src.core.exception_handler import not_found_exception_handler

        request = MagicMock(spec=Request)
        exc = NotFoundError("Resource not found")

        response = await not_found_exception_handler(request, exc)
        assert response.status_code == 404


class TestDatabaseExceptionHandler:
    async def test_database_exception_handler(self):
        from src.core.exception_handler import database_exception_handler

        request = MagicMock(spec=Request)
        exc = DatabaseError("Database failed")

        response = await database_exception_handler(request, exc)
        assert response.status_code == 500


class TestBusinessLogicExceptionHandler:
    async def test_business_logic_exception_handler(self):
        from src.core.exception_handler import business_logic_exception_handler

        request = MagicMock(spec=Request)
        exc = BusinessLogicError("Logic error")

        response = await business_logic_exception_handler(request, exc)
        assert response.status_code == 422


class TestStatsBoardExceptionHandler:
    async def test_statsboard_exception_handler_known_type(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = AuthenticationError("Auth failed")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 401

    async def test_statsboard_exception_handler_authorization_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = AuthorizationError("No permission")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 403

    async def test_statsboard_exception_handler_concurrency_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = ConcurrencyError("Locked")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 409

    async def test_statsboard_exception_handler_business_logic_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = BusinessLogicError("Invalid")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 422

    async def test_statsboard_exception_handler_external_service_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = ExternalServiceError("Service down")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 503

    async def test_statsboard_exception_handler_configuration_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = ConfigurationError("Config missing")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500

    async def test_statsboard_exception_handler_file_operation_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = FileOperationError("File error")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500

    async def test_statsboard_exception_handler_parsing_error(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = ParsingError("Parse failed")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 400

    async def test_statsboard_exception_handler_custom_exception(self):
        from src.core.exception_handler import statsboard_exception_handler

        request = MagicMock(spec=Request)
        exc = StatsBoardException("Custom error")

        response = await statsboard_exception_handler(request, exc)
        assert response.status_code == 500


class TestIntegrityErrorHandler:
    async def test_integrity_error_handler(self):
        from src.core.exception_handler import integrity_error_handler

        request = MagicMock(spec=Request)
        from sqlalchemy.exc import IntegrityError

        exc = IntegrityError("test", {}, Exception())

        response = await integrity_error_handler(request, exc)
        assert response.status_code == 409


class TestSQLAlchemyErrorHandler:
    async def test_sqlalchemy_error_handler(self):
        from src.core.exception_handler import sqlalchemy_error_handler

        request = MagicMock(spec=Request)
        from sqlalchemy.exc import SQLAlchemyError

        exc = SQLAlchemyError("DB error")

        response = await sqlalchemy_error_handler(request, exc)
        assert response.status_code == 500


class TestValueErrorHandler:
    async def test_value_error_handler(self):
        from src.core.exception_handler import value_error_handler

        request = MagicMock(spec=Request)
        exc = ValueError("Invalid value")

        response = await value_error_handler(request, exc)
        assert response.status_code == 400


class TestKeyErrorHandler:
    async def test_key_error_handler(self):
        from src.core.exception_handler import key_error_handler

        request = MagicMock(spec=Request)
        exc = KeyError("missing_key")

        response = await key_error_handler(request, exc)
        assert response.status_code == 400


class TestTypeErrorHandler:
    async def test_type_error_handler(self):
        from src.core.exception_handler import type_error_handler

        request = MagicMock(spec=Request)
        exc = TypeError("Invalid type")

        response = await type_error_handler(request, exc)
        assert response.status_code == 400


class TestConnectionErrorHandler:
    async def test_connection_error_handler(self):
        from src.core.exception_handler import connection_error_handler

        request = MagicMock(spec=Request)
        exc = ConnectionError("Cannot connect")

        response = await connection_error_handler(request, exc)
        assert response.status_code == 503


class TestTimeoutErrorHandler:
    async def test_timeout_error_handler(self):
        from src.core.exception_handler import timeout_error_handler

        request = MagicMock(spec=Request)
        exc = TimeoutError("Timed out")

        response = await timeout_error_handler(request, exc)
        assert response.status_code == 504


class TestGlobalExceptionHandler:
    async def test_global_exception_handler(self):
        from src.core.exception_handler import global_exception_handler

        request = MagicMock(spec=Request)
        exc = RuntimeError("Unexpected error")

        response = await global_exception_handler(request, exc)
        assert response.status_code == 500


class TestRegisterExceptionHandlers:
    def test_register_exception_handlers(self):
        from fastapi import FastAPI

        from src.core.exception_handler import register_exception_handlers

        app = FastAPI()
        initial_handlers = len(app.exception_handlers)

        register_exception_handlers(app)

        assert len(app.exception_handlers) > initial_handlers
