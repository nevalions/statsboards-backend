from io import BytesIO
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from src.helpers.file_system_service import FileSystemService
from src.helpers.upload_service import UploadService


class TestUploadService:
    """Test suite for UploadService."""

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
    def upload_service(self, fs_service):
        """Create an UploadService instance."""
        return UploadService(fs_service)

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

    @pytest.mark.asyncio
    async def test_sanitize_filename(self, upload_service):
        """Test filename sanitization."""
        result = await upload_service.sanitize_filename("  my file  ")
        assert result == "my_file"

    @pytest.mark.asyncio
    async def test_sanitize_filename_with_spaces(self, upload_service):
        """Test filename sanitization with multiple spaces."""
        result = await upload_service.sanitize_filename("  test   image   file  ")
        assert result == "test___image___file"

    @pytest.mark.asyncio
    async def test_sanitize_filename_with_cyrillic(self, upload_service):
        """Test filename sanitization with Cyrillic characters."""
        result = await upload_service.sanitize_filename("мирандов_леонид.jpg")
        assert result.isascii()
        assert "_" in result
        assert ".jpg" in result

    @pytest.mark.asyncio
    async def test_sanitize_filename_with_mixed_chars(self, upload_service):
        """Test filename sanitization with mixed characters."""
        result = await upload_service.sanitize_filename("test_файл@#$%.jpg")
        assert result.isascii()
        assert all(c.isalnum() or c in "._-" for c in result)

    @pytest.mark.asyncio
    async def test_get_timestamp(self, upload_service):
        """Test timestamp generation."""
        timestamp = await upload_service.get_timestamp()
        assert len(timestamp) == 14
        assert timestamp.isdigit()

    @pytest.mark.asyncio
    async def test_get_filename(self, upload_service, sample_upload_file):
        """Test filename generation with timestamp."""
        timestamp = "20231205123456"
        filename = await upload_service.get_filename(timestamp, sample_upload_file)
        assert filename == f"{timestamp}_test_image.jpg"

    @pytest.mark.asyncio
    async def test_is_image_type_valid(self, upload_service, sample_upload_file):
        """Test image type validation with valid image."""
        await upload_service.is_image_type(sample_upload_file)

    @pytest.mark.asyncio
    async def test_is_image_type_invalid(self, upload_service):
        """Test image type validation with invalid file type."""
        upload_file = Mock()
        upload_file.content_type = "application/pdf"
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.is_image_type(upload_file)
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_file_size_valid(self, upload_service):
        """Test file size validation with valid size."""
        upload_file = Mock(spec=UploadFile)
        upload_file.file = BytesIO(b"test data")
        await upload_service.validate_file_size(upload_file)

    @pytest.mark.asyncio
    async def test_validate_file_size_too_large(self, upload_service):
        """Test file size validation with file exceeding max size."""
        upload_file = Mock(spec=UploadFile)
        large_size = 11 * 1024 * 1024  # 11MB
        large_data = b"x" * large_size
        upload_file.file = BytesIO(large_data)
        with pytest.raises(HTTPException) as exc_info:
            await upload_service.validate_file_size(upload_file)
        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_file(self, upload_service, temp_upload_dir):
        """Test uploading file."""
        dest = temp_upload_dir / "test.jpg"
        upload_file = Mock(spec=UploadFile)
        upload_file.file = BytesIO(b"test data")

        await upload_service.upload_file(dest, upload_file)
        assert dest.exists()

    @pytest.mark.asyncio
    async def test_upload_file_error(self, upload_service, temp_upload_dir):
        """Test uploading file with error."""
        dest = temp_upload_dir / "test.jpg"
        upload_file = Mock(spec=UploadFile)
        upload_file.file = Mock(side_effect=OSError("Disk full"))

        with pytest.raises(HTTPException) as exc_info:
            await upload_service.upload_file(dest, upload_file)
        assert exc_info.value.status_code == 400
        assert "An error occurred while uploading file" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_image_and_return_data(
        self, upload_service, sample_upload_file, temp_upload_dir
    ):
        """Test uploading image and returning data."""
        sub_folder = "test_images"
        data = await upload_service.upload_image_and_return_data(
            sub_folder, sample_upload_file
        )

        assert isinstance(data, dict)
        assert "dest" in data
        assert "filename" in data
        assert "timestamp" in data
        assert "upload_dir" in data
        assert data["dest"].exists()
        assert "test_images" in str(data["upload_dir"])

    @pytest.mark.asyncio
    async def test_save_upload_image(self, upload_service, sample_upload_file):
        """Test saving uploaded image."""
        sub_folder = "test_save"
        result = await upload_service.save_upload_image(sample_upload_file, sub_folder)
        assert "test_save" in result
        assert ".jpg" in result
        assert result.startswith("/static/uploads/")
