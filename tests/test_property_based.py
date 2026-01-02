"""
Property-based tests for critical helper functions using Hypothesis.

These tests verify that functions maintain their expected properties
across a wide range of random inputs, catching edge cases that
traditional example-based tests might miss.

Run with:
    pytest tests/test_property_based.py
"""


import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.helpers.image_processing_service import ImageProcessingService
from src.helpers.text_helpers import convert_cyrillic_filename, safe_int_conversion


@pytest.mark.property
class TestSafeIntConversion:
    """Property-based tests for safe_int_conversion function."""

    @given(st.integers(min_value=-999999, max_value=999999))
    def test_valid_integer_conversion(self, number):
        """Should correctly convert valid integer strings."""
        result = safe_int_conversion(str(number))
        assert result == number

    @given(st.text())
    def test_invalid_input_returns_zero(self, text):
        """Should return 0 for any non-numeric input."""
        result = safe_int_conversion(text)
        assume(not text.lstrip("-").strip().isdigit() or text in ["", "-", "--"])
        assert result == 0

    @given(st.integers(min_value=-9999, max_value=9999))
    def test_negative_numbers(self, number):
        """Should correctly handle negative numbers."""
        result = safe_int_conversion(str(number))
        assert result == number

    @given(
        st.text(
            min_size=1,
            max_size=10,
            alphabet="0123456789"
        )
    )
    def test_large_numbers(self, number_str):
        """Should handle large positive integers."""
        assume(len(number_str) > 0)
        result = safe_int_conversion(number_str)
        assert result == int(number_str)

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_whitespace_handling(self, text):
        """Should handle leading/trailing whitespace."""
        assume(text.strip().lstrip("-").isdigit() if text.strip() else False)
        try:
            expected = int(text.strip())
        except ValueError:
            return
        result = safe_int_conversion(f"  {text}  ")
        assert result == expected


@pytest.mark.property
class TestHexToRGB:
    """Property-based tests for hex_to_rgb function."""

    @given(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )
    def test_valid_6_char_hex(self, r, g, b):
        """Should correctly parse 6-character hex colors."""
        image_service = ImageProcessingService()
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        result = image_service.hex_to_rgb(hex_color)
        assert result == (r, g, b)

    @given(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )
    def test_valid_8_char_hex(self, r, g, b):
        """Should correctly parse 8-character hex colors (ignoring alpha)."""
        image_service = ImageProcessingService()
        alpha = 255
        hex_color = f"#{r:02x}{g:02x}{b:02x}{alpha:02x}"
        result = image_service.hex_to_rgb(hex_color)
        assert result == (r, g, b)

    @given(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )
    def test_without_hash_prefix(self, r, g, b):
        """Should handle hex without # prefix."""
        image_service = ImageProcessingService()
        hex_color = f"{r:02x}{g:02x}{b:02x}"
        result = image_service.hex_to_rgb(hex_color)
        assert result == (r, g, b)

    @given(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )
    def test_uppercase_hex(self, r, g, b):
        """Should handle uppercase hex values."""
        image_service = ImageProcessingService()
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        result = image_service.hex_to_rgb(hex_color)
        assert result == (r, g, b)

    @given(st.text(min_size=1, max_size=10))
    def test_invalid_length_returns_none(self, text):
        """Should return None for invalid lengths."""
        assume(len(text.replace("#", "")) not in [6, 8])
        image_service = ImageProcessingService()
        result = image_service.hex_to_rgb(text)
        assert result is None

    @given(st.text(alphabet="ghijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ", min_size=6, max_size=6))
    def test_invalid_characters_return_none(self, text):
        """Should return None for non-hex characters."""
        image_service = ImageProcessingService()
        result = image_service.hex_to_rgb(text)
        assert result is None

    @given(st.text())
    def test_range_property(self, text):
        """All returned values should be in valid RGB range."""
        image_service = ImageProcessingService()
        result = image_service.hex_to_rgb(text)
        if result is not None:
            r, g, b = result
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255


@pytest.mark.property
class TestConvertCyrillicFilename:
    """Property-based tests for convert_cyrillic_filename function."""

    @given(st.text())
    def test_idempotency(self, text):
        """Applying function twice should produce same result as once."""
        first_result = convert_cyrillic_filename(text)
        second_result = convert_cyrillic_filename(first_result)
        assert first_result == second_result

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"))
    def test_latin_only_passthrough(self, text):
        """Latin-only input should pass through unchanged."""
        result = convert_cyrillic_filename(text)
        assert result == text

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_space_replacement(self, text):
        """Spaces should be replaced with underscores."""
        assume(' ' in text)
        result = convert_cyrillic_filename(text)
        assert ' ' not in result

    @given(st.text())
    @settings(suppress_health_check=[HealthCheck.filter_too_much])
    def test_empty_string_handling(self, text):
        """Empty input should return empty output."""
        assume(len(text.strip()) == 0)
        result = convert_cyrillic_filename(text)
        assert result == ""
