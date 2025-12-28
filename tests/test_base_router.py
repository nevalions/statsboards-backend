import pytest
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from starlette import status

from src.core.base_router import MinimalBaseRouter
from src.core.response_schemas import ResponseModel


class DummySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class DummyService:
    """Mock service for testing."""

    def __init__(self):
        pass


class DummyModel(BaseModel):
    """Mock model for testing."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TestMinimalBaseRouter:
    """Test suite for MinimalBaseRouter."""

    def test_create_response_with_valid_item(self):
        """Test create_response with valid item returns dict."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        item = DummyModel(id=1, name="Test Item")
        result = router.create_response(item, "Test message")

        assert result["content"] is not None
        assert result["content"]["id"] == 1
        assert result["content"]["name"] == "Test Item"
        assert result["type"] == "text"
        assert result["message"] == "Test message"
        assert result["status_code"] == status.HTTP_200_OK
        assert result["success"] is True

    def test_create_response_with_none_raises_exception(self):
        """Test create_response with None raises HTTPException."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        with pytest.raises(HTTPException) as exc_info:
            router.create_response(None, "Not found")

        assert exc_info.value.status_code == 404
        assert "ELEMENT NOT FOUND" in exc_info.value.detail

    def test_create_response_with_custom_type(self):
        """Test create_response with custom type parameter."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        item = DummyModel(id=2, name="Another Item")
        result = router.create_response(item, "Custom type", _type="json")

        assert result["type"] == "json"
        assert result["success"] is True
        assert result["content"]["id"] == 2

    def test_create_pydantic_response_with_valid_item(self):
        """Test create_pydantic_response with valid item returns ResponseModel."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        item = DummyModel(id=3, name="Pydantic Item")
        result = router.create_pydantic_response(item, "Success message")

        assert isinstance(result, ResponseModel)
        assert result.success is True
        assert result.status_code == status.HTTP_200_OK
        assert result.type == "text"
        assert result.message == "Success message"
        assert result.content is not None
        assert result.content.id == 3
        assert result.content.name == "Pydantic Item"

    def test_create_pydantic_response_with_none_raises_exception(self):
        """Test create_pydantic_response with None raises HTTPException."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        with pytest.raises(HTTPException) as exc_info:
            router.create_pydantic_response(None, "Not found")

        assert exc_info.value.status_code == 404
        assert "ELEMENT NOT FOUND" in exc_info.value.detail

    def test_route_creates_router(self):
        """Test that route method creates and returns a router."""
        router = MinimalBaseRouter(
            prefix="/test",
            tags=["test"],
            service=DummyService(),
        )

        result = router.route()

        assert result is not None
        assert hasattr(result, "prefix")
        assert result.prefix == "/test"
        assert result.tags == ["test"]
