import os
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from fastapi import UploadFile
from PIL import Image

from src.core.config import uploads_path
from src.logging_config import get_logger
from src.helpers.file_system_service import FileSystemService
from src.helpers.upload_service import UploadService
from src.helpers.download_service import DownloadService
from src.helpers.image_processing_service import ImageProcessingService


class ResizedImagesPaths(TypedDict):
    original: str
    icon: str
    webview: str


class DownloadedAndResizedImagesPaths(TypedDict):
    main_path: str
    image_path: str
    image_url: str
    image_icon_url: str
    image_webview_url: str


class FileService:
    def __init__(
        self,
        upload_dir: Path = Path(__file__).resolve().parent.parent.parent
        / "static/uploads",
    ):
        self.fs_service = FileSystemService(upload_dir)
        self.upload_service = UploadService(self.fs_service)
        self.download_service = DownloadService(self.fs_service)
        self.image_service = ImageProcessingService()
        self.logger = get_logger("backend_logger_fileservice", self)
        self.logger.debug("Initializing FileService")

    async def sanitize_filename(self, filename: str) -> str:
        return await self.upload_service.sanitize_filename(filename)

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str) -> str:
        return await self.upload_service.save_upload_image(upload_file, sub_folder)

    async def save_and_resize_upload_image(
        self,
        upload_file: UploadFile,
        sub_folder: str,
        icon_height: int = 100,
        web_view_height: int = 400,
    ) -> ResizedImagesPaths:
        self.logger.debug(
            f"Saving image for subfolder: {sub_folder} "
            f"and resize it for icon:{icon_height} and webview:{web_view_height}"
        )

        data = await self.upload_service.upload_image_and_return_data(
            sub_folder, upload_file
        )

        original_dest = data["dest"]
        original_filename = data["filename"]
        timestamp = data["timestamp"]
        upload_dir = data["upload_dir"]

        image = await self.image_service.open_image_from_path(str(original_dest))

        icon_filename = await self.image_service.resize_and_save_image(
            icon_height,
            image,
            timestamp,
            upload_dir,
            original_filename,
            "icon",
        )

        webview_filename = await self.image_service.resize_and_save_image(
            web_view_height,
            image,
            timestamp,
            upload_dir,
            original_filename,
            "webview",
        )

        try:
            rel_original_dest = Path("/static/uploads") / sub_folder / original_filename
            rel_icon_dest = Path("/static/uploads") / sub_folder / icon_filename
            rel_webview_dest = Path("/static/uploads") / sub_folder / webview_filename

            final_urls = {
                "original": str(rel_original_dest),
                "icon": str(rel_icon_dest),
                "webview": str(rel_webview_dest),
            }

            self.logger.info(
                f"URLs for uploaded and resized images generated: {final_urls}"
            )
            return final_urls
        except Exception as e:
            self.logger.error(
                f"Generating resized image for subfolder: {sub_folder} {e}",
                exc_info=True,
            )
            raise

    async def get_most_common_color(self, image_path: str) -> str | None:
        return await self.image_service.get_most_common_color(image_path)

    async def download_image(self, img_url: str, path_with_image_name: str) -> str:
        return await self.download_service.download_image(img_url, path_with_image_name)

    async def open_file_from_path(self, file_path: str) -> dict[str, bytes]:
        return await self.download_service.open_file(file_path)

    async def open_image_from_file(self, file_data: bytes) -> Image.Image:
        return await self.image_service.open_image_from_file(file_data)

    async def open_image_from_path(self, image_path: str) -> Image.Image:
        return await self.image_service.open_image_from_path(image_path)

    async def download_and_resize_image(
        self,
        img_url: str,
        original_file_path: str,
        original_image_path_with_filename: str,
        icon_image_path: str,
        web_view_image_path: str,
        icon_height: int = 100,
        web_view_height: int = 400,
    ) -> None:
        self.logger.debug(f"Initialize download and resize image from {img_url}")
        self.logger.debug(
            f"to full path with image filename {original_image_path_with_filename}"
        )

        image_path = await self.download_service.download_image(
            img_url, original_image_path_with_filename
        )
        self.logger.debug(f"img_path: {image_path}")
        file_data = await self.download_service.open_file(image_path)
        image = await self.image_service.open_image_from_file(file_data["data"])

        icon_dir = str(Path(icon_image_path).parent)
        await self.fs_service.create_path(icon_dir)
        self.logger.debug(f"Created icon directory: {icon_dir}")
        icon_filename = Path(icon_image_path).name
        await self.image_service.resize_and_save_image(
            icon_height,
            image,
            None,
            Path(icon_dir),
            icon_filename,
            "",
        )

        webview_dir = str(Path(web_view_image_path).parent)
        await self.fs_service.create_path(webview_dir)
        self.logger.debug(f"Created webview directory: {webview_dir}")
        webview_filename = Path(web_view_image_path).name
        await self.image_service.resize_and_save_image(
            web_view_height,
            image,
            None,
            Path(webview_dir),
            webview_filename,
            "",
        )

    @staticmethod
    def _generate_image_paths(
        image_url: str,
        image_type_prefix: str,
        image_title: str,
        icon_height: int,
        web_view_height: int,
    ) -> dict[str, str]:
        path = urlparse(image_url).path
        ext = Path(path).suffix

        image_filename = image_title.strip().replace(" ", "_")
        icon_filename = f"{image_filename}_{icon_height}px{ext}"
        webview_filename = f"{image_filename}_{web_view_height}px{ext}"

        main_path = f"{image_type_prefix}"
        image_path = os.path.join(uploads_path, f"{main_path}{image_filename}{ext}")
        icon_path = os.path.join(uploads_path, f"{main_path}{icon_filename}")
        webview_path = os.path.join(uploads_path, f"{main_path}{webview_filename}")

        static_uploads_path = "/static/uploads/"
        relative_image_url = os.path.join(
            static_uploads_path, main_path, f"{image_filename}{ext}"
        )
        relative_icon_url = os.path.join(static_uploads_path, main_path, icon_filename)
        relative_webview_url = os.path.join(
            static_uploads_path, main_path, webview_filename
        )

        return {
            "main_path": main_path,
            "image_path": image_path,
            "icon_path": icon_path,
            "webview_path": webview_path,
            "relative_image_url": relative_image_url,
            "relative_icon_url": relative_icon_url,
            "relative_webview_url": relative_webview_url,
        }

    async def download_and_process_image(
        self,
        img_url: str,
        image_type_prefix: str,
        image_title: str,
        icon_height: int,
        web_view_height: int,
    ) -> DownloadedAndResizedImagesPaths:
        self.logger.debug("Starting download and processing of image")

        paths = self._generate_image_paths(
            img_url, image_type_prefix, image_title, icon_height, web_view_height
        )
        self.logger.debug(f"Generated paths: {paths}")

        await self.download_and_resize_image(
            img_url=img_url,
            original_file_path=paths["main_path"],
            original_image_path_with_filename=paths["image_path"],
            icon_image_path=paths["icon_path"],
            web_view_image_path=paths["webview_path"],
            icon_height=icon_height,
            web_view_height=web_view_height,
        )

        final_paths_processed = {
            "main_path": paths["main_path"],
            "image_path": paths["image_path"],
            "image_url": paths["relative_image_url"],
            "image_icon_url": paths["relative_icon_url"],
            "image_webview_url": paths["relative_webview_url"],
        }

        self.logger.info(f"Final processed paths: {final_paths_processed}")
        return final_paths_processed


file_service = FileService()
