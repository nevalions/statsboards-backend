import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from aiohttp import ClientSession

from src.helpers.download_service import DownloadService
from src.helpers.file_system_service import FileSystemService


class TestDownloadService:
    """Test suite for DownloadService."""

    @pytest.fixture
    def temp_upload_dir(self, tmp_path):
        """Create a temporary upload directory for testing."""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @pytest.fixture
    def fs_service(self, temp_upload_dir):
        """Create a FileSystemService instance."""
        return FileSystemService(temp_upload_dir)

    @pytest.fixture
    def download_service(self, fs_service):
        """Create a DownloadService instance."""
        return DownloadService(fs_service)

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_image_data_from_url_success(self, mock_get, download_service):
        """Test fetching image data from URL successfully."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake_image_data")
        mock_get.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/image.jpg"
        result = await download_service.fetch_image_data_from_url(img_url)
        assert result == b"fake_image_data"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_image_data_from_url_failure(self, mock_get, download_service):
        """Test fetching image data from URL with error."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status = Mock(side_effect=Exception("Not found"))
        mock_get.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/notfound.jpg"
        with pytest.raises(Exception):
            await download_service.fetch_image_data_from_url(img_url)

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image(self, mock_fetch, download_service, tmp_path):
        """Test downloading image from URL."""
        mock_fetch.return_value = b"fake_image_data"

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        result = await download_service.download_image(img_url, path_with_image_name)
        assert result == path_with_image_name
        assert Path(path_with_image_name).exists()
        assert Path(path_with_image_name).read_bytes() == b"fake_image_data"

    @pytest.mark.asyncio
    async def test_open_file(self, download_service, tmp_path):
        """Test opening file from path."""
        file_path = tmp_path / "test_file.txt"
        test_data = b"test data"
        file_path.write_bytes(test_data)

        result = await download_service.open_file(str(file_path))
        assert isinstance(result, dict)
        assert "filename" in result
        assert "data" in result
        assert result["filename"] == "test_file.txt"
        assert result["data"] == test_data
