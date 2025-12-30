from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
from PIL import Image

from src.helpers.image_processing_service import ImageProcessingService


class TestImageProcessingService:
    """Test suite for ImageProcessingService."""

    @pytest.fixture
    def image_service(self):
        """Create an ImageProcessingService instance."""
        return ImageProcessingService()

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        image = Image.new("RGB", (100, 100), color="red")
        img_buffer = BytesIO()
        image.save(img_buffer, format="JPEG")
        img_buffer.seek(0)
        return img_buffer

    @pytest.mark.asyncio
    async def test_open_image_from_file(self, image_service, sample_image):
        """Test opening image from file data."""
        image = await image_service.open_image_from_file(sample_image.getvalue())
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_open_image_from_path(self, image_service, sample_image, tmp_path):
        """Test opening image from file path."""
        image_path = tmp_path / "test_open.jpg"
        with open(image_path, "wb") as f:
            f.write(sample_image.getvalue())

        image = await image_service.open_image_from_path(str(image_path))
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    @pytest.mark.asyncio
    async def test_save_image(self, image_service, tmp_path):
        """Test saving image to destination."""
        save_image = Image.new("RGB", (50, 50), color="green")
        source_image = Image.new("RGB", (50, 50), color="green")
        dest = tmp_path / "saved_image.jpg"

        await image_service.save_image(dest, save_image, source_image)
        assert dest.exists()

    @pytest.mark.asyncio
    async def test_save_image_error(self, image_service):
        """Test saving image with invalid path raises error."""
        save_image = Image.new("RGB", (50, 50), color="green")
        source_image = Image.new("RGB", (50, 50), color="green")
        dest = Path("/nonexistent/path/image.jpg")

        with pytest.raises(HTTPException) as exc_info:
            await image_service.save_image(dest, save_image, source_image)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_resize_image(self, image_service, sample_image):
        """Test image resizing."""
        image = Image.open(sample_image)
        height = 50
        resized_image = await image_service.resize_image(image, height)
        assert resized_image.height == 50
        assert resized_image.width == 50

    @pytest.mark.asyncio
    async def test_resize_and_save(self, image_service, sample_image, tmp_path):
        """Test resizing and saving image."""
        image = Image.open(sample_image)
        height = 50
        dest = tmp_path / "resized_image.jpg"

        await image_service.resize_and_save(dest, "resized_image.jpg", height, image)
        assert dest.exists()

        resized_image = Image.open(dest)
        assert resized_image.height == 50

    @pytest.mark.asyncio
    async def test_generate_filename(self, image_service):
        """Test filename generation."""
        timestamp = "20231205123456"
        _type = "icon"
        file_name = "resized_img"
        upload_file_filename = "test.jpg"

        result = await image_service.generate_filename(
            _type, file_name, timestamp, upload_file_filename
        )
        assert result == f"{timestamp}_{_type}_{upload_file_filename}"

    @pytest.mark.asyncio
    async def test_generate_filename_without_type(self, image_service):
        """Test filename generation without type."""
        timestamp = "20231205123456"
        _type = None
        file_name = "resized_img"
        upload_file_filename = "test.jpg"

        result = await image_service.generate_filename(
            _type, file_name, timestamp, upload_file_filename
        )
        assert result == f"{timestamp}_{upload_file_filename}"

    @pytest.mark.asyncio
    async def test_resize_and_save_image(self, image_service, tmp_path):
        """Test resizing and saving image."""
        image = Image.new("RGB", (200, 200), color="blue")
        timestamp = "20231205123456"
        upload_dir = tmp_path
        upload_file_filename = "test.jpg"
        _type = "icon"

        result = await image_service.resize_and_save_image(
            100, image, timestamp, upload_dir, upload_file_filename, _type
        )
        assert "icon" in result
        assert "test.jpg" in result
        assert (upload_dir / result).exists()

    def test_hex_to_rgb(self, image_service):
        """Test converting hex color to RGB."""
        result = image_service.hex_to_rgb("#FF0000")
        assert result == (255, 0, 0)

        result = image_service.hex_to_rgb("#00FF00")
        assert result == (0, 255, 0)

        result = image_service.hex_to_rgb("#0000FF")
        assert result == (0, 0, 255)

    def test_hex_to_rgb_without_hash(self, image_service):
        """Test converting hex color without hash prefix."""
        result = image_service.hex_to_rgb("FF0000")
        assert result == (255, 0, 0)

    def test_hex_to_rgb_invalid(self, image_service):
        """Test converting invalid hex color returns None."""
        result = image_service.hex_to_rgb("invalid")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_most_common_color_rgb(self, image_service, tmp_path):
        """Test getting most common color from RGB image."""
        image = Image.new("RGB", (10, 10), color=(255, 0, 0))
        image_path = tmp_path / "color_test.png"
        image.save(image_path)

        color = await image_service.get_most_common_color(str(image_path))
        assert color == "#ff0000"

    @pytest.mark.asyncio
    async def test_get_most_common_color_rgba(self, image_service, tmp_path):
        """Test getting most common color from RGBA image."""
        image = Image.new("RGBA", (10, 10), color=(0, 255, 0, 255))
        image_path = tmp_path / "rgba_test.png"
        image.save(image_path)

        color = await image_service.get_most_common_color(str(image_path))
        assert color == "#00ff00"

    @pytest.mark.asyncio
    async def test_get_most_common_color_excluded_colors(self, image_service, tmp_path):
        """Test getting most common color with excluded colors."""
        image = Image.new("RGB", (10, 10), color=(0, 0, 0))
        image_path = tmp_path / "black_test.jpg"
        image.save(image_path)

        color = await image_service.get_most_common_color(str(image_path))
        assert color is None
