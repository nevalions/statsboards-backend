import pytest
from fastapi.testclient import TestClient

from src.core.exceptions import (
    BusinessLogicError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from src.main import app

client = TestClient(app)


class TestExceptionHandlers:
    def test_validation_error_handler(self):
        """Test ValidationError is caught and returns 400"""
        response = client.get("/test/raise-validation-error")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["success"] is False

    def test_not_found_error_handler(self):
        """Test NotFoundError is caught and returns 404"""
        response = client.get("/test/raise-not-found-error")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["success"] is False

    def test_database_error_handler(self):
        """Test DatabaseError is caught and returns 500"""
        response = client.get("/test/raise-database-error")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["success"] is False

    def test_business_logic_error_handler(self):
        """Test BusinessLogicError is caught and returns 422"""
        response = client.get("/test/raise-business-logic-error")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert data["success"] is False


class TestBuiltInExceptionHandlers:
    def test_value_error_handler(self):
        """Test ValueError is caught and returns 400"""
        response = client.get("/test/raise-value-error")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert data["type"] == "ValueError"

    def test_key_error_handler(self):
        """Test KeyError is caught and returns 400"""
        response = client.get("/test/raise-key-error")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "type" == "KeyError"

    def test_global_exception_handler(self):
        """Test unexpected exceptions return 500"""
        response = client.get("/test/raise-unexpected-error")
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["type"] in data
