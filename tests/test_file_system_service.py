from pathlib import Path

import pytest

from src.helpers.file_system_service import FileSystemService


class TestFileSystemService:
    """Test suite for FileSystemService."""

    @pytest.fixture
    def temp_upload_dir(self, tmp_path):
        """Create a temporary upload directory for testing."""
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    @pytest.fixture
    def fs_service(self, temp_upload_dir):
        """Create a FileSystemService instance with temporary upload directory."""
        return FileSystemService(temp_upload_dir)

    def test_init(self, temp_upload_dir):
        """Test FileSystemService initialization."""
        service = FileSystemService(temp_upload_dir)
        assert service.base_upload_dir == temp_upload_dir
        assert service.base_upload_dir.exists()
        assert service.logger is not None

    @pytest.mark.asyncio
    async def test_get_upload_dir(self, fs_service):
        """Test getting upload directory."""
        sub_folder = "test_folder"
        upload_dir = await fs_service.get_upload_dir(sub_folder)
        expected = fs_service.base_upload_dir / sub_folder
        assert upload_dir == expected

    @pytest.mark.asyncio
    async def test_create_upload_dir(self, fs_service):
        """Test creating upload directory."""
        sub_folder = "new_folder"
        upload_dir = fs_service.base_upload_dir / sub_folder

        await fs_service.create_upload_dir(sub_folder, upload_dir)
        assert upload_dir.exists()
        assert upload_dir.is_dir()

    @pytest.mark.asyncio
    async def test_get_and_create_upload_dir(self, fs_service):
        """Test getting and creating upload directory."""
        sub_folder = "combined_folder"
        upload_dir = await fs_service.get_and_create_upload_dir(sub_folder)
        expected = fs_service.base_upload_dir / sub_folder
        assert upload_dir == expected
        assert upload_dir.exists()

    @pytest.mark.asyncio
    async def test_get_destination_with_filename(self, fs_service):
        """Test getting destination path with filename."""
        upload_dir = fs_service.base_upload_dir
        filename = "test_file.jpg"
        dest = await fs_service.get_destination_with_filename(filename, upload_dir)
        assert dest == upload_dir / filename

    @pytest.mark.asyncio
    async def test_ensure_directory_created(self, fs_service, tmp_path):
        """Test ensuring directory is created."""
        image_path = str(tmp_path / "images" / "test.jpg")
        await fs_service.ensure_directory_created(image_path)
        assert Path(image_path).parent.exists()

    @pytest.mark.asyncio
    async def test_create_path(self, fs_service, tmp_path):
        """Test creating directory path."""
        path = str(tmp_path / "new" / "nested" / "directory" / "file.txt")
        result = await fs_service.create_path(path)
        assert result == path
        assert Path(path).parent.exists()

    @pytest.mark.asyncio
    async def test_save_file(self, fs_service, tmp_path):
        """Test saving data to file."""
        file_path = tmp_path / "test_file.txt"
        data = b"test data"
        await fs_service.save_file(str(file_path), data)
        assert file_path.exists()
        assert file_path.read_bytes() == data

    @pytest.mark.asyncio
    async def test_save_file_error(self, fs_service):
        """Test saving file with invalid path raises error."""
        with pytest.raises(Exception):
            await fs_service.save_file("/nonexistent/path/file.txt", b"data")

    @pytest.mark.asyncio
    async def test_open_file(self, fs_service, tmp_path):
        """Test opening file from path."""
        file_path = tmp_path / "test_file.txt"
        test_data = b"test data"
        file_path.write_bytes(test_data)

        result = await fs_service.open_file(str(file_path))
        assert isinstance(result, dict)
        assert "filename" in result
        assert "data" in result
        assert result["filename"] == "test_file.txt"
        assert result["data"] == test_data

    @pytest.mark.asyncio
    async def test_open_file_error(self, fs_service):
        """Test opening non-existent file raises error."""
        with pytest.raises(Exception):
            await fs_service.open_file("/nonexistent/path/file.txt")
