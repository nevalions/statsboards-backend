"""
Tests for core decorators.

Run with:
    pytest tests/test_decorators.py
"""

import asyncio
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.core.decorators import handle_service_exceptions
from src.core.exceptions import BusinessLogicError, NotFoundError


class MockService:
    """Mock service for testing."""

    def __init__(self):
        self.logger = Mock()
        self.model = Mock(__name__="TestModel")


class TestHandleServiceExceptions:
    """Tests for handle_service_exceptions decorator."""

    def test_async_wrapper_success(self):
        """Test successful async method execution."""
        decorator = handle_service_exceptions(operation="test_operation")

        async def test_method(self, value):
            return f"success: {value}"

        wrapped_method = decorator(test_method)
        service = MockService()

        result = asyncio.run(wrapped_method(service, "test_value"))

        assert result == "success: test_value"

    def test_sync_wrapper_success(self):
        """Test successful sync method execution."""
        decorator = handle_service_exceptions(operation="test_operation")

        def test_method(self, value):
            return f"success: {value}"

        wrapped_method = decorator(test_method)
        service = MockService()

        result = wrapped_method(service, "test_value")

        assert result == "success: test_value"

    def test_async_wrapper_http_exception_passthrough(self):
        """Test HTTPException is passed through."""
        decorator = handle_service_exceptions(operation="test_operation")

        async def test_method(self):
            raise HTTPException(status_code=400, detail="Bad request")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 400

    def test_sync_wrapper_http_exception_passthrough(self):
        """Test HTTPException is passed through in sync context."""
        decorator = handle_service_exceptions(operation="test_operation")

        def test_method(self):
            raise HTTPException(status_code=400, detail="Bad request")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            wrapped_method(service)

        assert exc_info.value.status_code == 400

    def test_async_wrapper_integrity_error(self):
        """Test IntegrityError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="create")

        async def test_method(self):
            raise IntegrityError("unique constraint violation", None, None)

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 409
        assert "Conflict" in exc_info.value.detail
        service.logger.error.assert_called_once()

    def test_sync_wrapper_integrity_error(self):
        """Test IntegrityError is caught and converted to HTTPException in sync."""
        decorator = handle_service_exceptions(operation="create")

        def test_method(self):
            raise IntegrityError("unique constraint violation", None, None)

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            wrapped_method(service)

        assert exc_info.value.status_code == 409
        service.logger.error.assert_called_once()

    def test_async_wrapper_sqlalchemy_error(self):
        """Test SQLAlchemyError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="update")

        async def test_method(self):
            raise SQLAlchemyError("database connection failed")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 500
        assert "Database error" in exc_info.value.detail
        service.logger.error.assert_called_once()

    def test_async_wrapper_value_error(self):
        """Test ValueError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="process")

        async def test_method(self):
            raise ValueError("Invalid value")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 400
        assert "Invalid data" in exc_info.value.detail
        service.logger.warning.assert_called_once()

    def test_async_wrapper_key_error(self):
        """Test KeyError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="process")

        async def test_method(self):
            raise KeyError("Missing key")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 400

    def test_async_wrapper_type_error(self):
        """Test TypeError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="process")

        async def test_method(self):
            raise TypeError("Wrong type")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 400

    def test_async_wrapper_not_found_error_reraise(self):
        """Test NotFoundError reraises as HTTPException when reraise_not_found=True."""
        decorator = handle_service_exceptions(operation="get", reraise_not_found=True)

        async def test_method(self):
            raise NotFoundError("Item not found")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 404
        service.logger.info.assert_called_once()

    def test_async_wrapper_not_found_error_return_value(self):
        """Test NotFoundError returns value when reraise_not_found=False."""
        decorator = handle_service_exceptions(
            operation="get", return_value_on_not_found={"default": "value"}
        )

        async def test_method(self):
            raise NotFoundError("Item not found")

        wrapped_method = decorator(test_method)
        service = MockService()

        result = asyncio.run(wrapped_method(service))

        assert result == {"default": "value"}
        service.logger.info.assert_called_once()

    def test_async_wrapper_not_found_error_return_none(self):
        """Test NotFoundError returns None when no return value specified."""
        decorator = handle_service_exceptions(operation="get")

        async def test_method(self):
            raise NotFoundError("Item not found")

        wrapped_method = decorator(test_method)
        service = MockService()

        result = asyncio.run(wrapped_method(service))

        assert result is None

    def test_async_wrapper_business_logic_error(self):
        """Test BusinessLogicError is caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="process")

        async def test_method(self):
            raise BusinessLogicError("Invalid business logic")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 422
        assert "Business logic error" in exc_info.value.detail
        service.logger.error.assert_called_once()

    def test_async_wrapper_unexpected_exception(self):
        """Test unexpected exceptions are caught and converted to HTTPException."""
        decorator = handle_service_exceptions(operation="process")

        async def test_method(self):
            raise RuntimeError("Unexpected error")

        wrapped_method = decorator(test_method)
        service = MockService()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail
        service.logger.critical.assert_called_once()

    def test_custom_item_name_without_model(self):
        """Test custom item name is used when service has no model."""
        decorator = handle_service_exceptions(item_name="CustomItem", operation="create")

        async def test_method(self):
            raise IntegrityError("test", None, None)

        wrapped_method = decorator(test_method)
        service = Mock()
        service.logger = Mock()
        delattr(service, "model")

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert "CustomItem" in exc_info.value.detail

    def test_service_without_logger(self):
        """Test decorator works when service has no logger."""
        decorator = handle_service_exceptions(operation="test", item_name="TestItem")

        async def test_method(self):
            raise IntegrityError("test", None, None)

        wrapped_method = decorator(test_method)

        class ServiceWithoutLogger:
            pass

        service = ServiceWithoutLogger()

        with pytest.raises(HTTPException):
            asyncio.run(wrapped_method(service))

    def test_service_without_model(self):
        """Test decorator uses default item name when no model."""
        decorator = handle_service_exceptions(operation="test")

        async def test_method(self):
            raise IntegrityError("test", None, None)

        wrapped_method = decorator(test_method)

        class ServiceWithoutModel:
            logger = Mock()

        service = ServiceWithoutModel()

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(wrapped_method(service))

        assert "item" in exc_info.value.detail

    def test_wrapper_preserves_function_name_and_docstring(self):
        """Test that wrapper preserves function metadata."""
        decorator = handle_service_exceptions(operation="test")

        async def test_method(self, value):
            """Test method docstring."""
            return value

        wrapped_method = decorator(test_method)

        assert wrapped_method.__name__ == "test_method"
        assert wrapped_method.__doc__ == "Test method docstring."
