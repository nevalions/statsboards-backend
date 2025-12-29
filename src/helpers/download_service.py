import os
from typing import Any

from aiohttp import ClientSession

from src.logging_config import get_logger
from src.helpers.file_system_service import FileSystemService


class DownloadService:
    def __init__(self, fs_service: FileSystemService):
        self.fs_service = fs_service
        self.logger = get_logger("backend_logger_download", self)

    async def fetch_image_data_from_url(self, img_url: str) -> bytes:
        self.logger.debug(f"Fetching image from {img_url}")
        try:
            async with ClientSession() as session:
                async with session.get(img_url) as response:
                    self.logger.debug(f"Response received: {response}")
                    if response.status != 200:
                        self.logger.info(f"Response status code: {response.status}")
                        response.raise_for_status()
                    return await response.read()
        except Exception as e:
            self.logger.error(f"Error fetching image from {img_url}: {e}")
            raise

    async def download_image(
        self, img_url: str, path_with_image_name: str
    ) -> str:
        self.logger.debug(f"Downloading image from {img_url} to {path_with_image_name}")
        try:
            image_data = await self.fetch_image_data_from_url(img_url)
            await self.fs_service.ensure_directory_created(path_with_image_name)
            await self.fs_service.save_file(path_with_image_name, image_data)
            return path_with_image_name
        except Exception as e:
            self.logger.error(
                f"Error downloading image from {img_url} to {path_with_image_name}: {e}",
                exc_info=True,
            )
            raise

    async def open_file(self, file_path: str) -> dict[str, Any]:
        return await self.fs_service.open_file(file_path)
