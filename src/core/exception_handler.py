from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .exceptions import (
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

EXCEPTION_MAPPING: dict[type[Exception], tuple[int, str]] = {
    ValueError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    KeyError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    TypeError: (status.HTTP_400_BAD_REQUEST, "Bad Request"),
    ValidationError: (status.HTTP_400_BAD_REQUEST, "Validation Error"),
    NotFoundError: (status.HTTP_404_NOT_FOUND, "Not Found"),
    AuthenticationError: (status.HTTP_401_UNAUTHORIZED, "Unauthorized"),
    AuthorizationError: (status.HTTP_403_FORBIDDEN, "Forbidden"),
    ConcurrencyError: (status.HTTP_409_CONFLICT, "Conflict"),
    IntegrityError: (status.HTTP_409_CONFLICT, "Conflict"),
    DatabaseError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Database Error"),
    SQLAlchemyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Database Error"),
    BusinessLogicError: (status.HTTP_422_UNPROCESSABLE_ENTITY, "Unprocessable Entity"),
    ExternalServiceError: (status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable"),
    ConfigurationError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "Configuration Error"),
    FileOperationError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "File Operation Error"),
    ParsingError: (status.HTTP_400_BAD_REQUEST, "Parsing Error"),
}


def create_error_response(
    status_code: int, detail: str, exc_type: str | None = None
) -> JSONResponse:
    """Create standardized error response"""
    content: dict[str, Any] = {"detail": detail, "success": False}
    if exc_type:
        content["type"] = exc_type
    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=exc.message,
        exc_type="ValidationError",
    )


async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors"""
    return create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=exc.message,
        exc_type="NotFoundError",
    )


async def database_exception_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors"""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed",
        exc_type="DatabaseError",
    )


async def business_logic_exception_handler(
    request: Request, exc: BusinessLogicError
) -> JSONResponse:
    """Handle business logic errors"""
    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=exc.message,
        exc_type="BusinessLogicError",
    )


async def statsboard_exception_handler(request: Request, exc: StatsBoardException) -> JSONResponse:
    """Handle all custom StatsBoard exceptions"""
    status_code, error_type = EXCEPTION_MAPPING.get(
        type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error")
    )
    return create_error_response(
        status_code=status_code,
        detail=exc.message,
        exc_type=error_type,
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors"""
    return create_error_response(
        status_code=status.HTTP_409_CONFLICT,
        detail="Resource already exists or violates constraints",
        exc_type="IntegrityError",
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors"""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed",
        exc_type="SQLAlchemyError",
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle value errors"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid data provided",
        exc_type="ValueError",
    )


async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle key errors"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Missing required field",
        exc_type="KeyError",
    )


async def type_error_handler(request: Request, exc: TypeError) -> JSONResponse:
    """Handle type errors"""
    return create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid data type",
        exc_type="TypeError",
    )


async def connection_error_handler(request: Request, exc: ConnectionError) -> JSONResponse:
    """Handle connection errors"""
    return create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Service unavailable - connection error",
        exc_type="ConnectionError",
    )


async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle timeout errors"""
    return create_error_response(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail="Operation timed out",
        exc_type="TimeoutError",
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle truly unexpected errors - should rarely trigger"""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
        exc_type=type(exc).__name__,
    )


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers with FastAPI app"""
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
    app.add_exception_handler(StatsBoardException, statsboard_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(KeyError, key_error_handler)
    app.add_exception_handler(TypeError, type_error_handler)
    app.add_exception_handler(ConnectionError, connection_error_handler)
    app.add_exception_handler(TimeoutError, timeout_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
