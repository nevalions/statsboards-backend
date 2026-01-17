"""
Tests for fetch helpers.

Run with:
    pytest tests/test_fetch_helpers.py
"""

import datetime
from unittest.mock import Mock


class TestInstanceToDict:
    """Tests for instance_to_dict function."""

    def test_instance_to_dict_filters_private_keys(self):
        """Test that instance_to_dict filters out keys starting with _."""
        from src.helpers.fetch_helpers import instance_to_dict

        instance = {
            "public": "value1",
            "_private": "value2",
            "another_public": "value3",
        }

        result = instance_to_dict(instance)

        assert result == {
            "public": "value1",
            "another_public": "value3",
        }
        assert "_private" not in result

    def test_instance_to_dict_empty_dict(self):
        """Test instance_to_dict with empty dictionary."""
        from src.helpers.fetch_helpers import instance_to_dict

        result = instance_to_dict({})

        assert result == {}

    def test_instance_to_dict_with_nested_dicts(self):
        """Test instance_to_dict with nested dictionaries."""
        from src.helpers.fetch_helpers import instance_to_dict

        instance = {
            "key1": "value1",
            "key2": {"nested": "value2"},
            "_private": "hidden",
        }

        result = instance_to_dict(instance)

        assert result["key1"] == "value1"
        assert result["key2"]["nested"] == "value2"
        assert "_private" not in result

    def test_instance_to_dict_exception_handling(self):
        """Test instance_to_dict handles exceptions gracefully."""
        from src.helpers.fetch_helpers import instance_to_dict

        instance = Mock()
        instance.items.side_effect = Exception("Test error")

        result = instance_to_dict(instance)

        assert result is None


class TestDeepDictConvert:
    """Tests for deep_dict_convert function."""

    def test_deep_dict_convert_with_datetime(self):
        """Test deep_dict_convert converts datetime to ISO format."""
        from src.helpers.fetch_helpers import deep_dict_convert

        test_datetime = datetime.datetime(2024, 1, 15, 12, 30, 45)
        instance = {
            "date_key": test_datetime,
            "string_key": "value",
        }

        result = deep_dict_convert(instance)

        assert result["date_key"] == test_datetime.isoformat()
        assert result["string_key"] == "value"

    def test_deep_dict_convert_with_nested_dict(self):
        """Test deep_dict_convert handles nested dictionaries."""
        from src.helpers.fetch_helpers import deep_dict_convert

        test_datetime = datetime.datetime(2024, 1, 15, 12, 30, 45)
        instance = {
            "outer": "value1",
            "nested": {
                "inner_date": test_datetime,
                "inner_string": "value2",
            },
        }

        result = deep_dict_convert(instance)

        assert result["outer"] == "value1"
        assert result["nested"]["inner_date"] == test_datetime.isoformat()
        assert result["nested"]["inner_string"] == "value2"

    def test_deep_dict_convert_filters_private_keys(self):
        """Test deep_dict_convert filters out keys starting with _."""
        from src.helpers.fetch_helpers import deep_dict_convert

        instance = {
            "public": "value1",
            "_private": "value2",
            "another_public": "value3",
        }

        result = deep_dict_convert(instance)

        assert result == {
            "public": "value1",
            "another_public": "value3",
        }
        assert "_private" not in result

    def test_deep_dict_convert_empty_dict(self):
        """Test deep_dict_convert with empty dictionary."""
        from src.helpers.fetch_helpers import deep_dict_convert

        result = deep_dict_convert({})

        assert result == {}

    def test_deep_dict_convert_exception_handling(self):
        """Test deep_dict_convert handles exceptions gracefully."""
        from src.helpers.fetch_helpers import deep_dict_convert

        instance = Mock()
        instance.items.side_effect = Exception("Test error")

        result = deep_dict_convert(instance)

        assert result is None
