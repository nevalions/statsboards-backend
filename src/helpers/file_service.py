import os
import shutil
from fileinput import filename
from typing import TypedDict, Any

from src.core.config import uploads_path
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO
from aiohttp import ClientSession
from datetime import datetime
from fastapi import UploadFile, HTTPException
from pathlib import Path

from src.logging_config import get_logger


class FileData(TypedDict):
    filename: str
    data: Any


class ImageData(TypedDict):
    dest: str
    filename: str
    timestamp: str
    upload_dir: Path | Any


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
        self.base_upload_dir = upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("backend_logger_fileservice", self)
        self.logger.debug(f"Initializing FileService")

    @staticmethod
    def sanitize_filename(self, filename):
        self.logger.debug(f"Sanitizing filename: {filename}")
        try:
            filename = filename.strip().replace(" ", "_")
            self.logger.debug(f"Sanitized filename: {filename}")
            return filename
        except Exception as e:
            self.logger.debug(f"Problem with sanitizing filename: {filename} {e}")

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str):
        self.logger.debug(f"Saving image for subfolder: {sub_folder}")
        data = await self.upload_image_and_return_data(sub_folder, upload_file)
        rel_dest = Path("/static/uploads") / sub_folder / data["filename"]
        self.logger.debug(f"Relative destination path: {rel_dest}")
        return str(rel_dest)

    async def get_destination_with_filename(self, filename, upload_dir):
        dest = upload_dir / filename
        self.logger.debug(f"original destination: {dest}")
        return dest

    async def get_and_create_upload_dir(self, sub_folder):
        upload_dir = await self.get_upload_dir(sub_folder)
        await self.create_upload_dir(sub_folder, upload_dir)
        return upload_dir

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

        data = await self.upload_image_and_return_data(sub_folder, upload_file)

        original_dest = data["dest"]
        original_filename = data["filename"]
        timestamp = data["timestamp"]
        upload_dir = data["upload_dir"]

        image = await self.open_image_from_path(original_dest)

        # Create and save the icon image
        icon_filename = await self.resize_and_save_resized_uploaded_image(
            icon_height,
            image,
            timestamp,
            upload_dir,
            upload_file.filename,
            "icon",
        )

        # Create and save the web view image
        webview_filename = await self.resize_and_save_resized_uploaded_image(
            web_view_height,
            image,
            timestamp,
            upload_dir,
            upload_file.filename,
            "webview",
        )

        # Construct relative path for all images
        try:
            rel_original_dest = Path("/static/uploads") / sub_folder / original_filename
            rel_icon_dest = Path("/static/uploads") / sub_folder / icon_filename
            rel_webview_dest = Path("/static/uploads") / sub_folder / webview_filename

            final_urls_for_uploaded_and_resized_image = {
                "original": str(rel_original_dest),
                "icon": str(rel_icon_dest),
                "webview": str(rel_webview_dest),
            }

            self.logger.info(
                f"URLs for uploaded and resized images generated: {final_urls_for_uploaded_and_resized_image}"
            )
            return final_urls_for_uploaded_and_resized_image
        except Exception as e:
            self.logger.error(
                f"Generating resized image for subfolder: {sub_folder} {e}"
            )

    async def resize_and_save_resized_downloaded_image(
        self,
        height: int,
        image: Any,
        timestamp: str | None,
        upload_dir: Path,
        upload_file_filename: str,
        _type: str,
    ):
        self.logger.debug("Start resizing downloaded image")
        file_name = "downloaded_img"
        file_name = await self._generate_filename(
            _type, file_name, timestamp, upload_file_filename
        )

        self.logger.debug(f"Downloaded Image filename: {file_name}")
        try:
            await self.final_image_resizer_and_save(
                upload_dir, file_name, height, image
            )
            return file_name
        except Exception as e:
            self.logger.error(f"Problem resizing downloaded image: {e}")

    async def resize_and_save_resized_uploaded_image(
        self,
        height: int,
        image: Any,
        timestamp: str | None,
        upload_dir: Path,
        upload_file_filename: str,
        _type: str,
    ):
        self.logger.debug("Start resizing uploaded image")
        file_name = "uploaded_img"
        file_name = await self._generate_filename(
            _type, file_name, timestamp, upload_file_filename
        )

        self.logger.debug(f"Uploaded Image filename: {file_name}")
        dest = upload_dir / file_name
        try:
            await self.final_image_resizer_and_save(dest, file_name, height, image)
            return file_name
        except Exception as e:
            self.logger.error(f"Problem resizing image: {e}")

    async def final_image_resizer_and_save(self, dest, file_name, height, image):
        try:
            width = int((image.width / image.height) * height)
        except Exception as e:
            self.logger.error(f"Problem getting width: {e}")
            raise
        try:
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            self.logger.error(f"Problem resizing image: {e}")
            raise

        await self.save_file_with_image_format_to_destination(
            dest, resized_image, image
        )
        self.logger.info(f"Resized image {file_name} saved to {dest}")

    async def _generate_filename(
        self, _type, file_name, timestamp, upload_file_filename
    ):
        self.logger.debug(f"Generating filename: {file_name}")
        if upload_file_filename:
            file_name = upload_file_filename
        if timestamp and upload_file_filename:
            file_name = f"{timestamp}_{upload_file_filename}"
        if timestamp and _type and upload_file_filename:
            file_name = f"{timestamp}_{_type}_{upload_file_filename}"
        self.logger.debug(f"Generated filename: {file_name}")
        return file_name

    async def save_file_with_image_format_to_destination(self, dest, save_image, image):
        self.logger.debug(f"Saving image to folder: {dest}")
        try:
            with dest.open("wb") as icon_buffer:
                save_image.save(icon_buffer, format=image.format)
            self.logger.info(f"image saved: {dest}")
        except Exception as e:
            self.logger.error(f"Problem saving image to: {save_image} {e}")
            raise HTTPException(
                status_code=400,
                detail="An error occurred while saving image.",
            )

    async def upload_image_and_return_data(self, sub_folder, upload_file) -> ImageData:
        upload_dir = await self.get_and_create_upload_dir(sub_folder)
        timestamp = await self.get_timestamp()
        original_filename = await self.get_filename(timestamp, upload_file)
        original_dest = await self.get_destination_with_filename(
            original_filename, upload_dir
        )
        await self.is_image_type(upload_file)
        await self.upload_image(original_dest, upload_file)
        self.logger.info(
            f"Data of uploaded image: "
            f"timestamp: {timestamp} filename: {original_filename}, "
            f"dest: {original_dest}, upload_dir: {upload_dir}"
        )
        return {
            "dest": original_dest,
            "filename": original_filename,
            "timestamp": timestamp,
            "upload_dir": upload_dir,
        }

    async def upload_image(self, original_dest, upload_file):
        try:
            with original_dest.open("wb") as buffer:
                self.logger.debug(f"Trying to save image")
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as ex:
            self.logger.error(
                f"Problem with saving image to destination {original_dest} {ex}"
            )
            raise HTTPException(
                status_code=400, detail="An error occurred while uploading file."
            )

    async def get_filename(self, timestamp, upload_file):
        original_filename = f"{timestamp}_{upload_file.filename}"
        self.logger.debug(f"original filename: {original_filename}")
        return original_filename

    async def get_upload_dir(self, sub_folder):
        upload_dir = self.base_upload_dir / sub_folder
        self.logger.debug(f"Saving image for subfolder: {sub_folder}")
        return upload_dir

    async def get_timestamp(self):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.logger.debug(f"Timestamp: {timestamp}")
        return timestamp

    async def create_upload_dir(self, sub_folder, upload_dir):
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory created for subfolder: {sub_folder}")
        except Exception as e:
            self.logger.error(
                f"Problem with saving image for subfolder: {sub_folder} {e}"
            )

    async def is_image_type(self, upload_file):
        if not upload_file.content_type.startswith("image/"):
            self.logger.error(f"Uploaded file type not an image")
            raise HTTPException(status_code=400, detail="Unsupported file type")

    async def get_most_common_color(self, image_path: str):
        self.logger.debug(f"Getting most common color: {image_path}")
        img = Image.open(image_path)

        # If the image has an alpha (transparency) channel, convert it to RGB
        if img.mode == "RGBA":
            self.logger.debug(f"Most common color: {img.mode}")
            temp_img = Image.new("RGB", img.size)
            temp_img.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = temp_img

        colors = img.convert("RGB").getcolors(
            img.size[0] * img.size[1]
        )  # Ensures RGB data
        if colors:
            colors.sort(key=lambda tup: tup[0], reverse=True)  # Sort by count
            # Exclude black, white, and certain specified colors
            excluded_colors = [
                {0},
                {255},
                {254, 254, 254},
                set(self.hex_to_rgb("#000105")),
                set(self.hex_to_rgb("#fdfdfd")),
                set(self.hex_to_rgb("#dfdfdf")),
                set(self.hex_to_rgb("#fcfcfc")),
            ]
            most_common_color = next(
                (color for count, color in colors if set(color) not in excluded_colors),
                None,
            )
            return (
                "#{:02x}{:02x}{:02x}".format(*most_common_color)
                if most_common_color
                else None
            )
        else:
            self.logger.warning(f"No common color detected")
            return None

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

    async def ensure_directory_created(self, image_path: str):
        self.logger.debug(f"Ensuring directory exists for path: {image_path}")
        try:
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            self.logger.debug(f"Directory created: {image_path}")
        except Exception as e:
            self.logger.error(f"Error creating directory for {image_path}: {e}")
            raise

    async def save_image_to_file(self, image_data: bytes, image_path: str):
        self.logger.debug(f"Saving image to file: {image_path}")
        try:
            with open(image_path, "wb") as fp:
                fp.write(image_data)
                self.logger.info(f"Image saved successfully: {image_path}")
        except Exception as e:
            self.logger.error(f"Error saving image to file {image_path}: {e}")
            raise

    async def download_image(
        self, img_url: str, path_with_image_name: str, original_path: str
    ) -> str:
        self.logger.debug(f"Downloading image from {img_url} to {path_with_image_name}")
        try:
            image_data = await self.fetch_image_data_from_url(img_url)
            await self.ensure_directory_created(path_with_image_name)
            await self.save_image_to_file(image_data, path_with_image_name)
            return path_with_image_name
        except Exception as e:
            self.logger.error(
                f"Error downloading image from {img_url} to {path_with_image_name}: {e}"
            )
            raise

    async def open_file_from_path(self, file_path: str) -> FileData:
        try:
            self.logger.debug(f"Opening file from {file_path}")
            with open(file_path, "rb") as file:
                file_data = file.read()
                try:
                    _filename = os.path.basename(file_path)
                    self.logger.debug(f"Filename: {_filename}")
                    return {"filename": _filename, "data": file_data}
                except Exception as e:
                    self.logger.error(f"Error opening file from {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error opening file from {file_path}: {e}")
            raise

    async def open_image_from_file(self, file):
        try:
            self.logger.debug(f"Opening image from file")
            image = Image.open(BytesIO(file))
        except Exception as e:
            self.logger.error(f"Error opening image from file: {e}")
            raise
        return image

    async def create_path(self, path: str) -> str:
        try:
            self.logger.debug(f"Creating path {path}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.logger.debug(f"Path created: {os.path.dirname(path)}")
            return path
        except Exception as e:
            self.logger.error(f"Error creating path {path}: {e}")
            raise

    async def open_image_from_path(self, image_path: str) -> Image:
        try:
            self.logger.debug(f"Opening image from {image_path}")
            with open(image_path, "rb") as file:
                image_data = file.read()
                return Image.open(BytesIO(image_data))
        except Exception as e:
            self.logger.error(f"Error opening image from {image_path}: {e}")
            raise

    async def download_and_resize_image(
        self,
        img_url: str,
        original_file_path: str,
        original_image_path_with_filename: str,
        icon_image_path: str,
        web_view_image_path: str,
        icon_height: int = 100,
        web_view_height: int = 400,
    ):
        self.logger.debug(f"Initialize download and resize image from {img_url}")
        self.logger.debug(
            f"to full path with image filename {original_image_path_with_filename}"
        )

        image_path = await self.download_image(
            img_url, original_image_path_with_filename, original_file_path
        )
        self.logger.debug(f"img_path: {image_path}")
        file = await self.open_file_from_path(image_path)
        image = await self.open_image_from_file(file["data"])

        created_icon_path = await self.create_path(icon_image_path)
        self.logger.debug(f"Created icon path: {created_icon_path}")
        await self.resize_and_save_resized_downloaded_image(
            icon_height,
            image,
            None,
            Path(created_icon_path),
            file["filename"],
            "icon",
        )

        created_web_view_path = await self.create_path(web_view_image_path)
        self.logger.debug(f"Created webview path: {created_web_view_path}")
        await self.resize_and_save_resized_downloaded_image(
            web_view_height,
            image,
            None,
            Path(created_web_view_path),
            file["filename"],
            "webview",
        )

    async def download_and_process_image(
        self,
        img_url: str,
        image_type_prefix: str,
        image_title: str,
        icon_height: int,
        web_view_height: int,
    ) -> DownloadedAndResizedImagesPaths:
        self.logger.debug("Starting download and processing of image")

        # Generate paths
        paths = self._generate_image_paths(
            img_url, image_type_prefix, image_title, icon_height, web_view_height
        )
        self.logger.debug(f"Generated paths: {paths}")

        # Download and resize the image
        await file_service.download_and_resize_image(
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

    @staticmethod
    def _generate_image_paths(
        image_url: str,
        image_type_prefix: str,
        image_title: str,
        icon_height: int,
        web_view_height: int,
    ) -> dict:
        path = urlparse(image_url).path
        ext = Path(path).suffix

        # Normalize filenames
        image_filename = image_title.strip().replace(" ", "_")
        icon_filename = f"{image_filename}_{icon_height}px{ext}"
        webview_filename = f"{image_filename}_{web_view_height}px{ext}"

        # Generate full paths
        main_path = f"{image_type_prefix}"
        image_path = os.path.join(uploads_path, f"{main_path}{image_filename}{ext}")
        icon_path = os.path.join(uploads_path, f"{main_path}{icon_filename}")
        webview_path = os.path.join(uploads_path, f"{main_path}{webview_filename}")

        # Generate relative paths for URLs
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

    def hex_to_rgb(self, hex_color: str):
        try:
            self.logger.debug(f"Converting hex color: {hex_color}")
            hex_color = hex_color.lstrip("#")
            # Convert the hex color to a tuple of integers and return it.
            final_color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            self.logger.info(f"Converted hex color: {final_color}")
            return final_color
        except Exception as e:
            self.logger.warning(f"Problem converting hex color: {hex_color} {e}")


file_service = FileService()
