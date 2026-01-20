"""Test photo_utils module."""

import pytest

from pathlib import Path

from src.helpers.photo_utils import photo_files_exist
from src.core.config import settings


@pytest.fixture
def mock_uploads_path(tmp_path):
    """Create a temporary uploads path for testing."""
    uploads_path = tmp_path / "uploads" / "persons" / "photos"
    uploads_path.mkdir(parents=True)
    return uploads_path


class TestPhotoFilesExist:
    """Test photo_files_exist function."""

    def test_none_url(self):
        """Test with None URL."""
        result = photo_files_exist(None)
        assert result is False

    def test_empty_string_url(self):
        """Test with empty string URL."""
        result = photo_files_exist("")
        assert result is False

    def test_no_files_exist(self, mock_uploads_path):
        """Test when no photo files exist."""
        url = "http://example.com/photos/player123.jpg"

        result = photo_files_exist(url)

        assert result is False

    def test_file_too_small(self, mock_uploads_path, monkeypatch):
        """Test when file is below minimum size."""
        photo_filename = "player123.jpg"

        (mock_uploads_path / photo_filename).write_bytes(b"small" * 512)

        url = f"http://example.com/photos/{photo_filename}"

        result = photo_files_exist(url)

        assert result is False

    def test_invalid_url_handling(self, mock_uploads_path, monkeypatch):
        """Test handling of invalid URL without filename."""
        url = "http://example.com/photos/invalid"

        result = photo_files_exist(url)

        assert result is False
