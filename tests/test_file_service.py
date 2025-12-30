import pytest
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
from unittest.mock import Mock, AsyncMock, patch
from PIL import Image
from io import BytesIO

from src.helpers.file_service import (
    FileService,
    ResizedImagesPaths,
    DownloadedAndResizedImagesPaths,
)
from src.helpers.download_service import DownloadService
from src.helpers.upload_service import UploadService
from src.helpers.file_system_service import FileSystemService


class TestFileService:
    """Test suite for FileService."""

    @pytest.fixture
    def temp_upload_dir(self, tmp_path):
        """Create a temporary upload directory for testing."""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @pytest.fixture
    def file_service(self, temp_upload_dir):
        """Create a FileService instance with temporary upload directory."""
        return FileService(upload_dir=temp_upload_dir)

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        image = Image.new("RGB", (100, 100), color="red")
        img_buffer = BytesIO()
        image.save(img_buffer, format="JPEG")
        img_buffer.seek(0)
        return img_buffer

    @pytest.fixture
    def sample_upload_file(self, sample_image):
        """Create a sample UploadFile object."""
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "test_image.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.file = sample_image
        return upload_file

    def test_init(self, temp_upload_dir):
        """Test FileService initialization."""
        service = FileService(upload_dir=temp_upload_dir)
        assert service.fs_service is not None
        assert service.upload_service is not None
        assert service.download_service is not None
        assert service.image_service is not None
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_sanitize_filename(self, file_service):
        """Test filename sanitization."""
        result = await file_service.sanitize_filename("  my file  ")
        assert result == "my_file"

    @pytest.mark.asyncio
    async def test_save_upload_image(self, file_service, sample_upload_file):
        """Test saving uploaded image."""
        sub_folder = "test_images"
        result = await file_service.save_upload_image(sample_upload_file, sub_folder)
        assert "test_images" in result
        assert ".jpg" in result

    @pytest.mark.asyncio
    async def test_save_and_resize_upload_image(self, file_service, sample_upload_file):
        """Test saving and resizing uploaded image."""
        sub_folder = "test_resize"
        result = await file_service.save_and_resize_upload_image(
            sample_upload_file, sub_folder, icon_height=50, web_view_height=100
        )
        assert isinstance(result, dict)
        assert "original" in result
        assert "icon" in result
        assert "webview" in result
        assert result["original"].endswith("test_image.jpg")
        assert "icon" in result["icon"]
        assert "webview" in result["webview"]

    @pytest.mark.asyncio
    async def test_get_most_common_color(self, file_service, tmp_path):
        """Test getting most common color from image."""
        image = Image.new("RGB", (10, 10), color=(255, 0, 0))
        image_path = tmp_path / "color_test.png"
        image.save(image_path)

        color = await file_service.get_most_common_color(str(image_path))
        assert color == "#ff0000"

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url", new_callable=AsyncMock)
    async def test_download_image(
        self, mock_fetch, file_service, tmp_path, sample_image
    ):
        """Test downloading image from URL."""
        large_image_data = sample_image.getvalue() * 20
        mock_fetch.return_value = large_image_data

        img_url = "http://example.com/image.jpg"
        path_with_image_name = str(tmp_path / "downloaded_image.jpg")

        result = await file_service.download_image(img_url, path_with_image_name)
        assert result == path_with_image_name
        assert Path(path_with_image_name).exists()

    @pytest.mark.asyncio
    async def test_open_file_from_path(self, file_service, tmp_path, sample_image):
        """Test opening file from path."""
        file_path = tmp_path / "test_file.txt"
        with open(file_path, "wb") as f:
            f.write(sample_image.getvalue())

        result = await file_service.open_file_from_path(str(file_path))
        assert isinstance(result, dict)
        assert "filename" in result
        assert "data" in result

    @pytest.mark.asyncio
    async def test_open_image_from_file(self, file_service, sample_image):
        """Test opening image from file data."""
        image = await file_service.open_image_from_file(sample_image.getvalue())
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_open_image_from_path(self, file_service, tmp_path, sample_image):
        """Test opening image from file path."""
        image_path = tmp_path / "test_open.jpg"
        with open(image_path, "wb") as f:
            f.write(sample_image.getvalue())

        image = await file_service.open_image_from_path(str(image_path))
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_download_and_resize_image(
        self, file_service, tmp_path, sample_image
    ):
        """Test downloading and resizing image."""
        img_url = "http://example.com/image.jpg"
        original_file_path = str(tmp_path / "images")
        original_image_path = str(tmp_path / "images" / "image.jpg")
        icon_image_path = str(tmp_path / "images" / "icon_100px.jpg")
        web_view_image_path = str(tmp_path / "images" / "webview_400px.jpg")

        tmp_path.joinpath("images").mkdir(parents=True, exist_ok=True)
        tmp_path.joinpath("images/image.jpg").write_bytes(sample_image.getvalue())

        with patch.object(
            file_service.download_service,
            "download_image",
            return_value=original_image_path,
        ):
            with patch.object(
                file_service.fs_service, "create_path", side_effect=lambda x: x
            ):
                with patch.object(
                    file_service.image_service,
                    "resize_and_save_image",
                    new_callable=AsyncMock,
                ):
                    await file_service.download_and_resize_image(
                        img_url,
                        original_file_path,
                        original_image_path,
                        icon_image_path,
                        web_view_image_path,
                        icon_height=100,
                        web_view_height=400,
                    )

    @staticmethod
    def test_generate_image_paths():
        """Test static method for generating image paths."""
        image_url = "http://example.com/path/to/image.jpg"
        image_type_prefix = "teams/"
        image_title = "test team"
        icon_height = 100
        web_view_height = 400

        result = FileService._generate_image_paths(
            image_url, image_type_prefix, image_title, icon_height, web_view_height
        )

        assert isinstance(result, dict)
        assert "main_path" in result
        assert "image_path" in result
        assert "icon_path" in result
        assert "webview_path" in result
        assert "relative_image_url" in result
        assert "relative_icon_url" in result
        assert "relative_webview_url" in result
        assert "test_team_100px.jpg" in result["icon_path"]
        assert "test_team_400px.jpg" in result["webview_path"]

    @staticmethod
    def test_generate_image_paths_without_extension():
        """Test generating image paths when URL has no extension."""
        image_url = "http://example.com/path/to/image"
        image_type_prefix = "teams/"
        image_title = "test team"
        icon_height = 100
        web_view_height = 400

        result = FileService._generate_image_paths(
            image_url, image_type_prefix, image_title, icon_height, web_view_height
        )

        assert result["icon_path"].endswith("_100px")
        assert result["webview_path"].endswith("_400px")

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url", new_callable=AsyncMock)
    async def test_download_and_process_image(
        self, mock_fetch, file_service, sample_image
    ):
        """Test downloading and processing image."""
        mock_fetch.return_value = sample_image.getvalue()

        img_url = "http://example.com/image.jpg"
        image_type_prefix = "teams/"
        image_title = "test team"
        icon_height = 100
        web_view_height = 400

        with patch.object(
            file_service, "download_and_resize_image", new_callable=AsyncMock
        ):
            result = await file_service.download_and_process_image(
                img_url, image_type_prefix, image_title, icon_height, web_view_height
            )
            assert isinstance(result, dict)
            assert "main_path" in result
            assert "image_path" in result
            assert "image_url" in result
            assert "image_icon_url" in result
            assert "image_webview_url" in result

    @pytest.mark.asyncio
    @patch.object(DownloadService, "download_image", new_callable=AsyncMock)
    async def test_download_and_resize_image_with_force_redownload(
        self, mock_download, file_service, tmp_path, sample_image
    ):
        """Test download_and_resize_image with force_redownload parameter."""
        img_url = "http://example.com/image.jpg"
        original_file_path = str(tmp_path / "images")
        original_image_path = str(tmp_path / "images" / "image.jpg")
        icon_image_path = str(tmp_path / "images" / "icon_100px.jpg")
        web_view_image_path = str(tmp_path / "images" / "webview_400px.jpg")

        tmp_path.joinpath("images").mkdir(parents=True, exist_ok=True)
        tmp_path.joinpath("images/image.jpg").write_bytes(sample_image.getvalue() * 20)

        mock_download.return_value = original_image_path

        with patch.object(
            file_service.fs_service, "create_path", side_effect=lambda x: x
        ):
            with patch.object(
                file_service.image_service,
                "resize_and_save_image",
                new_callable=AsyncMock,
            ):
                await file_service.download_and_resize_image(
                    img_url,
                    original_file_path,
                    original_image_path,
                    icon_image_path,
                    web_view_image_path,
                    icon_height=100,
                    web_view_height=400,
                    force_redownload=True,
                )
                mock_download.assert_called_once_with(
                    img_url, original_image_path, force_redownload=True
                )

    @pytest.mark.asyncio
    @patch.object(DownloadService, "fetch_image_data_from_url", new_callable=AsyncMock)
    @patch.object(DownloadService, "download_image", new_callable=AsyncMock)
    async def test_download_and_process_image_with_force_redownload(
        self, mock_download, mock_fetch, file_service, sample_image
    ):
        """Test download_and_process_image with force_redownload parameter."""
        mock_fetch.return_value = sample_image.getvalue()
        mock_download.return_value = "/path/to/image.jpg"

        img_url = "http://example.com/image.jpg"
        image_type_prefix = "teams/"
        image_title = "test team"
        icon_height = 100
        web_view_height = 400

        with patch.object(
            file_service, "download_and_resize_image", new_callable=AsyncMock
        ) as mock_download_resize:
            result = await file_service.download_and_process_image(
                img_url,
                image_type_prefix,
                image_title,
                icon_height,
                web_view_height,
                force_redownload=True,
            )
            assert isinstance(result, dict)
            mock_download_resize.assert_called_once()
            call_kwargs = mock_download_resize.call_args.kwargs
            assert call_kwargs.get("force_redownload") is True

    @pytest.mark.asyncio
    async def test_generate_image_paths_with_cyrillic_title(self):
        """Test generating image paths with Cyrillic title."""
        image_url = "http://example.com/path/to/image.jpg"
        image_type_prefix = "teams/"
        image_title = "Команда"
        icon_height = 100
        web_view_height = 400

        result = FileService._generate_image_paths(
            image_url, image_type_prefix, image_title, icon_height, web_view_height
        )

        assert isinstance(result, dict)
        assert "Komanda_100px.jpg" in result["icon_path"]
        assert "Komanda_400px.jpg" in result["webview_path"]
        assert "Komanda.jpg" in result["image_path"]


class TestUploadService:
    """Test suite for UploadService."""

    @pytest.fixture
    def temp_upload_dir(self, tmp_path):
        """Create a temporary upload directory for testing."""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @pytest.fixture
    def file_system_service(self, temp_upload_dir):
        """Create a FileSystemService instance."""
        return FileSystemService(base_upload_dir=temp_upload_dir)

    @pytest.fixture
    def upload_service(self, file_system_service):
        """Create an UploadService instance."""
        return UploadService(file_system_service)

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        image = Image.new("RGB", (100, 100), color="red")
        img_buffer = BytesIO()
        image.save(img_buffer, format="JPEG")
        img_buffer.seek(0)
        return img_buffer

    @pytest.fixture
    def sample_upload_file_cyrillic(self, sample_image):
        """Create a sample UploadFile with Cyrillic filename."""
        upload_file = Mock(spec=UploadFile)
        upload_file.filename = "команда.jpg"
        upload_file.content_type = "image/jpeg"
        upload_file.file = sample_image
        return upload_file

    @pytest.mark.asyncio
    async def test_upload_with_cyrillic_filename(
        self, upload_service, temp_upload_dir, sample_upload_file_cyrillic
    ):
        """Test uploading file with Cyrillic filename."""
        sub_folder = "test_images"

        result = await upload_service.upload_image_and_return_data(
            sub_folder, sample_upload_file_cyrillic
        )

        assert "filename" in result
        filename = result["filename"]
        assert filename.endswith(".jpg")
        assert "komanda" in filename.lower()
        assert result["dest"].exists()
