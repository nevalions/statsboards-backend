import pytest
from datetime import datetime
from src.core.models.base import BaseServiceDB
from src.core.models.mixins import SerializationMixin
from src.seasons.db_services import SeasonServiceDB
from src.logging_config import setup_logging

setup_logging()


class TestSerializationMixin:
    """Test suite for SerializationMixin methods."""

    def test_is_des_ascending(self):
        """Test is_des method with ascending order."""
        from sqlalchemy import asc

        result = SerializationMixin.is_des(False, asc("test"))
        assert result is not None

    def test_is_des_descending(self):
        """Test is_des method with descending order."""
        from sqlalchemy import desc

        result = SerializationMixin.is_des(True, desc("test"))
        assert result is not None

    def test_is_des_exception(self):
        """Test is_des method raises exception on invalid input."""
        result = SerializationMixin.is_des(True, "invalid")
        assert result is None

    def test_default_serializer_datetime(self):
        """Test default_serializer with datetime object."""
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        result = SerializationMixin.default_serializer(test_datetime)
        assert result == "2023-01-01T12:00:00"

    def test_default_serializer_unsupported_type(self):
        """Test default_serializer with unsupported type."""
        result = SerializationMixin.default_serializer({"key": "value"})
        assert result is None

    def test_to_dict_model_instance(self, test_db, season_sample):
        """Test to_dict with SQLAlchemy model instance."""
        result = SerializationMixin.to_dict(season_sample)
        assert isinstance(result, dict)
        assert "year" in result
        assert "description" in result
        assert "_sa_instance_state" not in result

    def test_to_dict_already_dict(self):
        """Test to_dict with dict input."""
        test_dict = {"key": "value", "number": 42}
        result = SerializationMixin.to_dict(test_dict)
        assert result == test_dict

    def test_to_dict_unsupported_type(self):
        """Test to_dict with unsupported type."""
        result = SerializationMixin.to_dict("string_value")
        assert result is None

    def test_to_dict_nested_model(self, test_db, tournament):
        """Test to_dict with model that has relationships."""
        result = SerializationMixin.to_dict(tournament)
        assert isinstance(result, dict)
        assert "id" in result
        assert "title" in result
        assert "_sa_instance_state" not in result
