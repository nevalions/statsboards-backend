"""
Tests for fetch helpers.

Run with:
    pytest tests/test_fetch_helpers.py
"""

import datetime
from unittest.mock import Mock

from src.core.enums import InitialTimeMode


class TestInitialGameclockHelpers:
    def test_calculate_initial_gameclock_seconds_for_max_mode(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=720,
            initial_time_mode=InitialTimeMode.MAX,
            initial_time_min_seconds=None,
        )

        assert result == 720

    def test_calculate_initial_gameclock_seconds_for_max_mode_non_default_regression(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=900,
            initial_time_mode=InitialTimeMode.MAX,
            initial_time_min_seconds=None,
        )

        assert result == 900

    def test_calculate_initial_gameclock_seconds_for_zero_mode(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=720,
            initial_time_mode=InitialTimeMode.ZERO,
            initial_time_min_seconds=None,
        )

        assert result == 0

    def test_calculate_initial_gameclock_seconds_for_min_mode(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=720,
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=120,
        )

        assert result == 120

    def test_calculate_initial_gameclock_seconds_for_min_mode_45_minutes(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=3600,
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=2700,
        )

        assert result == 2700

    def test_calculate_initial_gameclock_seconds_clamps_to_gameclock_max(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=1800,
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=2700,
        )

        assert result == 1800

    def test_calculate_initial_gameclock_seconds_clamps_negative_to_zero_without_max(self):
        from src.helpers.fetch_helpers import _calculate_initial_gameclock_seconds

        result = _calculate_initial_gameclock_seconds(
            gameclock_max=None,
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=-10,
        )

        assert result == 0

    def test_get_preset_values_for_gameclock_uses_initial_time_mode(self):
        from src.helpers.fetch_helpers import _get_preset_values_for_gameclock

        preset = Mock(
            gameclock_max=900,
            initial_time_mode=InitialTimeMode.MIN,
            initial_time_min_seconds=45,
            direction="down",
            on_stop_behavior="hold",
        )

        result = _get_preset_values_for_gameclock(preset)

        assert result["gameclock"] == 45
        assert result["gameclock_time_remaining"] == 45
        assert result["gameclock_max"] == 900

    def test_get_preset_values_for_gameclock_zero_mode(self):
        from src.helpers.fetch_helpers import _get_preset_values_for_gameclock

        preset = Mock(
            gameclock_max=900,
            initial_time_mode=InitialTimeMode.ZERO,
            initial_time_min_seconds=None,
            direction="down",
            on_stop_behavior="hold",
        )

        result = _get_preset_values_for_gameclock(preset)

        assert result["gameclock"] == 0
        assert result["gameclock_time_remaining"] == 0

    def test_get_preset_values_for_gameclock_max_mode_non_default_regression(self):
        from src.helpers.fetch_helpers import _get_preset_values_for_gameclock

        preset = Mock(
            gameclock_max=900,
            initial_time_mode=InitialTimeMode.MAX,
            initial_time_min_seconds=None,
            direction="down",
            on_stop_behavior="hold",
        )

        result = _get_preset_values_for_gameclock(preset)

        assert result["gameclock"] == 900
        assert result["gameclock_time_remaining"] == 900
        assert result["gameclock_max"] == 900


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

    def test_deep_dict_convert_with_list_of_objects(self):
        """Test deep_dict_convert handles lists of objects with __dict__."""
        from src.helpers.fetch_helpers import deep_dict_convert

        class MockObject:
            def __init__(self):
                self.id = 1
                self.name = "Test"
                self._private = "hidden"

        instance = {
            "players": [MockObject(), MockObject()],
            "count": 2,
        }

        result = deep_dict_convert(instance)

        assert isinstance(result["players"], list)
        assert len(result["players"]) == 2
        assert result["players"][0]["id"] == 1
        assert result["players"][0]["name"] == "Test"
        assert "_private" not in result["players"][0]
        assert result["count"] == 2

    def test_deep_dict_convert_with_nested_objects(self):
        """Test deep_dict_convert handles nested objects with __dict__."""
        from src.helpers.fetch_helpers import deep_dict_convert

        class NestedObject:
            def __init__(self):
                self.id = 1
                self.value = "nested"

        class ParentObject:
            def __init__(self):
                self.id = 2
                self.name = "parent"
                self.nested = NestedObject()

        instance = {
            "parent": ParentObject(),
        }

        result = deep_dict_convert(instance)

        assert result["parent"]["id"] == 2
        assert result["parent"]["name"] == "parent"
        assert result["parent"]["nested"]["id"] == 1
        assert result["parent"]["nested"]["value"] == "nested"

    def test_deep_dict_convert_with_dict_containing_objects(self):
        """Test deep_dict_convert handles dicts containing objects."""
        from src.helpers.fetch_helpers import deep_dict_convert

        class MockPlayer:
            def __init__(self):
                self.id = 1
                self.name = "Player"

        instance = {
            "match_id": 1,
            "players": [
                {"id": 1, "player": MockPlayer(), "team": {"name": "Team A"}},
                {"id": 2, "player": MockPlayer(), "team": {"name": "Team B"}},
            ],
        }

        result = deep_dict_convert(instance)

        assert result["match_id"] == 1
        assert len(result["players"]) == 2
        assert result["players"][0]["player"]["name"] == "Player"
        assert result["players"][0]["team"]["name"] == "Team A"
        assert result["players"][1]["player"]["name"] == "Player"
        assert result["players"][1]["team"]["name"] == "Team B"
