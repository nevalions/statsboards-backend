from pydantic import BaseModel, ConfigDict
from starlette import status

from src.core.response_schemas import ResponseModel


class DummySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    value: int


class TestResponseModel:
    """Test suite for ResponseModel wrapper."""

    def test_success_response(self):
        """Test creating a success response."""
        content = DummySchema(id=1, name="Test", value=100)
        response = ResponseModel.success_response(content, "Operation successful")

        assert response.success is True
        assert response.status_code == status.HTTP_200_OK
        assert response.type == "text"
        assert response.message == "Operation successful"
        assert response.content is not None
        assert response.content.id == 1
        assert response.content.name == "Test"
        assert response.content.value == 100

    def test_success_response_default_message(self):
        """Test creating a success response with default message."""
        content = DummySchema(id=2, name="Test2", value=200)
        response = ResponseModel.success_response(content)

        assert response.message == "Operation successful"
        assert response.success is True

    def test_created_response(self):
        """Test creating a created response."""
        content = DummySchema(id=3, name="Test3", value=300)
        response = ResponseModel.created_response(content, "Resource created")

        assert response.success is True
        assert response.status_code == status.HTTP_201_CREATED
        assert response.type == "text"
        assert response.message == "Resource created"
        assert response.content.id == 3

    def test_created_response_default_message(self):
        """Test creating a created response with default message."""
        content = DummySchema(id=4, name="Test4", value=400)
        response = ResponseModel.created_response(content)

        assert response.message == "Resource created"
        assert response.status_code == status.HTTP_201_CREATED

    def test_not_found_response(self):
        """Test creating a not found response."""
        response = ResponseModel.not_found_response("Resource not found")

        assert response["success"] is False
        assert response["status_code"] == status.HTTP_404_NOT_FOUND
        assert response["content"] is None
        assert response["message"] == "Resource not found"

    def test_not_found_response_default_message(self):
        """Test creating a not found response with default message."""
        response = ResponseModel.not_found_response()

        assert response["message"] == "Resource not found"

    def test_response_model_serialization(self):
        """Test that ResponseModel can be serialized to dict."""
        content = DummySchema(id=5, name="Test5", value=500)
        response = ResponseModel.success_response(content)

        response_dict = response.model_dump()

        assert "content" in response_dict
        assert "type" in response_dict
        assert "message" in response_dict
        assert "status_code" in response_dict
        assert "success" in response_dict
        assert response_dict["success"] is True
        assert response_dict["content"]["id"] == 5
