from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

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
    @patch("aiohttp.ClientSession.head")
    async def test_get_remote_file_size_success(self, mock_head, download_service):
        """Test getting remote file size successfully."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Length": "12345"}
        mock_head.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/image.jpg"
        result = await download_service.get_remote_file_size(img_url)
        assert result == 12345

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.head")
    async def test_get_remote_file_size_no_content_length(
        self, mock_head, download_service
    ):
        """Test getting remote file size when Content-Length header is missing."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {}
        mock_head.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/image.jpg"
        result = await download_service.get_remote_file_size(img_url)
        assert result is None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.head")
    async def test_get_remote_file_size_non_200_status(
        self, mock_head, download_service
    ):
        """Test getting remote file size when status is not 200."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_head.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/image.jpg"
        result = await download_service.get_remote_file_size(img_url)
        assert result is None

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.head")
    async def test_get_remote_file_size_network_error(
        self, mock_head, download_service
    ):
        """Test getting remote file size when network error occurs."""
        mock_head.side_effect = Exception("Network error")

        img_url = "http://example.com/image.jpg"
        result = await download_service.get_remote_file_size(img_url)
        assert result is None

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
    async def test_fetch_image_data_from_url_with_retries(
        self, mock_get, download_service
    ):
        """Test fetching image data with retry logic on first failure."""
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.raise_for_status = Mock(
            side_effect=Exception("Server error")
        )

        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.read = AsyncMock(return_value=b"fake_image_data")

        mock_get.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success,
        ]

        img_url = "http://example.com/image.jpg"
        result = await download_service.fetch_image_data_from_url(
            img_url, max_retries=3
        )
        assert result == b"fake_image_data"
        assert mock_get.call_count == 2

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_fetch_image_data_from_url_failure(self, mock_get, download_service):
        """Test fetching image data from URL with error after all retries."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status = Mock(side_effect=Exception("Not found"))
        mock_get.return_value.__aenter__.return_value = mock_response

        img_url = "http://example.com/notfound.jpg"
        with pytest.raises(Exception, match="Not found"):
            await download_service.fetch_image_data_from_url(img_url, max_retries=2)

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image(self, mock_fetch, download_service, tmp_path):
        """Test downloading image from URL."""
        mock_fetch.return_value = b"fake_image_data" * 100

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        result = await download_service.download_image(img_url, path_with_image_name)
        assert result == path_with_image_name
        assert Path(path_with_image_name).exists()
        assert Path(path_with_image_name).read_bytes() == b"fake_image_data" * 100

    @pytest.mark.asyncio
    @patch.object(DownloadService, "get_remote_file_size")
    async def test_download_image_skip_when_exists_same_size(
        self, mock_remote_size, download_service, tmp_path
    ):
        """Test skipping download when file exists with same size."""
        existing_file = tmp_path / "existing_image.jpg"
        existing_file.write_bytes(b"x" * 2000)

        mock_remote_size.return_value = 2000

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(existing_file)

        result = await download_service.download_image(img_url, path_with_image_name)
        assert result == path_with_image_name
        assert existing_file.read_bytes() == b"x" * 2000
        mock_remote_size.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image_force_redownload(
        self, mock_fetch, download_service, tmp_path
    ):
        """Test forcing redownload when file already exists."""
        existing_file = tmp_path / "existing_image.jpg"
        existing_file.write_bytes(b"old_data" * 128)

        mock_fetch.return_value = b"new_data" * 128

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(existing_file)

        result = await download_service.download_image(
            img_url, path_with_image_name, force_redownload=True
        )
        assert result == path_with_image_name
        assert existing_file.read_bytes() == b"new_data" * 128
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image_file_size_below_minimum(
        self, mock_fetch, download_service, tmp_path
    ):
        """Test download fails when file size is below minimum."""
        mock_fetch.return_value = b"small"

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "small_image.jpg")

        with pytest.raises(ValueError, match="below minimum"):
            await download_service.download_image(
                img_url, path_with_image_name, min_file_size=1024
            )

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image_with_custom_min_file_size(
        self, mock_fetch, download_service, tmp_path
    ):
        """Test downloading image with custom minimum file size."""
        mock_fetch.return_value = b"valid_image_data" * 128

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        result = await download_service.download_image(
            img_url, path_with_image_name, min_file_size=100
        )
        assert result == path_with_image_name
        assert Path(path_with_image_name).exists()

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image_retry_on_failure(
        self, mock_fetch, download_service, tmp_path
    ):
        """Test download retries on first failure."""
        mock_fetch.side_effect = [Exception("Network error"), b"image_data" * 128]

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        result = await download_service.download_image(
            img_url, path_with_image_name, min_file_size=10
        )
        assert result == path_with_image_name
        assert Path(path_with_image_name).exists()
        assert Path(path_with_image_name).read_bytes() == b"image_data" * 128
        assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url")
    async def test_download_image_all_retries_fail(
        self, mock_fetch, download_service, tmp_path
    ):
        """Test download fails after all retries."""
        mock_fetch.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
        ]

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        with pytest.raises(Exception, match="Error 3"):
            await download_service.download_image(img_url, path_with_image_name)
        assert mock_fetch.call_count == 3

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
