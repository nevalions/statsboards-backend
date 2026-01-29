from pathlib import Path
from typing import Any

from src.logging_config import get_logger


class FileSystemService:
    def __init__(self, base_upload_dir: Path):
        self.base_upload_dir = base_upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("filesystem", self)

    async def get_upload_dir(self, sub_folder: str) -> Path:
        self.logger.debug(f"Getting upload directory for subfolder: {sub_folder}")
        return self.base_upload_dir / sub_folder

    async def create_upload_dir(self, sub_folder: str, upload_dir: Path) -> None:
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory created for subfolder: {sub_folder}")
        except Exception as e:
            self.logger.error(
                f"Problem creating directory for subfolder: {sub_folder} {e}",
                exc_info=True,
            )

    async def get_and_create_upload_dir(self, sub_folder: str) -> Path:
        upload_dir = await self.get_upload_dir(sub_folder)
        await self.create_upload_dir(sub_folder, upload_dir)
        return upload_dir

    async def get_destination_with_filename(self, filename: str, upload_dir: Path) -> Path:
        dest = upload_dir / filename
        self.logger.debug(f"Original destination: {dest}")
        return dest

    async def ensure_directory_created(self, image_path: str) -> None:
        self.logger.debug(f"Ensuring directory exists for path: {image_path}")
        try:
            Path(image_path).parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory created: {image_path}")
        except Exception as e:
            self.logger.error(f"Error creating directory for {image_path}: {e}")
            raise

    async def create_path(self, path: str) -> str:
        try:
            self.logger.debug(f"Creating path {path}")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Path created: {Path(path).parent}")
            return path
        except Exception as e:
            self.logger.error(f"Error creating path {path}: {e}", exc_info=True)
            raise

    async def save_file(self, file_path: str, data: bytes) -> None:
        try:
            with open(file_path, "wb") as fp:
                fp.write(data)
                self.logger.info(f"File saved successfully: {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving file to {file_path}: {e}", exc_info=True)
            raise

    async def open_file(self, file_path: str) -> dict[str, Any]:
        try:
            self.logger.debug(f"Opening file from {file_path}")
            with open(file_path, "rb") as file:
                file_data = file.read()
                filename = Path(file_path).name
                self.logger.debug(f"Filename: {filename}")
                return {"filename": filename, "data": file_data}
        except Exception as e:
            self.logger.error(f"Error opening file from {file_path}: {e}", exc_info=True)
            raise
