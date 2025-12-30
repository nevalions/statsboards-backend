import asyncio
import os
from pathlib import Path
from typing import Any

from aiohttp import ClientSession

from src.logging_config import get_logger
from src.helpers.file_system_service import FileSystemService


class DownloadService:
    def __init__(self, fs_service: FileSystemService):
        self.fs_service = fs_service
        self.logger = get_logger("backend_logger_download", self)

    async def fetch_image_data_from_url(self, img_url: str, max_retries: int = 3) -> bytes:
        self.logger.debug(f"Fetching image from {img_url}")
        
        for attempt in range(max_retries):
            try:
                async with ClientSession() as session:
                    async with session.get(img_url) as response:
                        self.logger.debug(f"Response received: {response}")
                        if response.status != 200:
                            self.logger.info(f"Response status code: {response.status}")
                            response.raise_for_status()
                        data = await response.read()
                        self.logger.debug(f"Successfully fetched {len(data)} bytes from {img_url}")
                        return data
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {img_url}: {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} attempts failed for {img_url}: {e}")
                    raise

    async def download_image(
        self, img_url: str, path_with_image_name: str, min_file_size: int = 1024
    ) -> str:
        self.logger.debug(f"Downloading image from {img_url} to {path_with_image_name}")
        
        for attempt in range(3):
            try:
                image_data = await self.fetch_image_data_from_url(img_url)
                
                if len(image_data) < min_file_size:
                    raise ValueError(
                        f"Downloaded file size {len(image_data)} bytes is below "
                        f"minimum {min_file_size} bytes"
                    )
                
                await self.fs_service.ensure_directory_created(path_with_image_name)
                await self.fs_service.save_file(path_with_image_name, image_data)
                
                file_size = len(image_data)
                self.logger.info(
                    f"Successfully downloaded image from {img_url} "
                    f"to {path_with_image_name} ({file_size} bytes)"
                )
                return path_with_image_name
                
            except ValueError as e:
                if attempt < 2:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/3 failed for {img_url}: {e}. "
                        f"Retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(
                        f"All 3 attempts failed for {img_url}: {e}",
                        exc_info=True,
                    )
                    raise
                    
            except Exception as e:
                if attempt < 2:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/3 failed for {img_url}: {e}. "
                        f"Retrying..."
                    )
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(
                        f"All 3 attempts failed for {img_url}: {e}",
                        exc_info=True,
                    )
                    raise

    async def open_file(self, file_path: str) -> dict[str, Any]:
        return await self.fs_service.open_file(file_path)
