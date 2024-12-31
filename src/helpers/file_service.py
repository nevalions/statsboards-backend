import os
import shutil
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


class ImageData(TypedDict):
    dest: str
    filename: str
    timestamp: str
    upload_dir: Path | Any


class ResizedImagesPaths(TypedDict):
    original: str
    icon: str
    webview: str


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

        # Open the image for resizing
        self.logger.debug(f"Opening destination file for resize: {original_dest}")
        with original_dest.open("rb") as image_file:
            try:
                image = Image.open(image_file)
                self.logger.debug(f"Image opened: {image}")
            except Exception as e:
                self.logger.error(
                    f"Problem opening image: {image} from {original_dest} {e}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="An error occurred while opening image for resize.",
                )

            # Create and save the icon image
            icon_filename = await self.resize_and_save_resized_image(
                icon_height, image, timestamp, upload_dir, upload_file, "icon"
            )

            # Create and save the web view image
            webview_filename = await self.resize_and_save_resized_image(
                web_view_height, image, timestamp, upload_dir, upload_file, "webview"
            )
            # _type = "webview"
            # webview_filename = f"{timestamp}_{_type}_{upload_file.filename}"
            # webview_dest = upload_dir / webview_filename
            # webview_width = int((image.width / image.height) * web_view_height)
            # webview_image = image.resize(
            #     (webview_width, web_view_height), Image.Resampling.LANCZOS
            # )
            #
            # await self.save_file_with_image_format_to_destination(
            #     webview_dest, webview_image, image
            # )

        # Construct relative path for all images
        rel_original_dest = Path("/static/uploads") / sub_folder / original_filename
        rel_icon_dest = Path("/static/uploads") / sub_folder / icon_filename
        rel_webview_dest = Path("/static/uploads") / sub_folder / webview_filename

        # Create a dictionary to return the paths of all the image versions created
        return {
            "original": str(rel_original_dest),
            "icon": str(rel_icon_dest),
            "webview": str(rel_webview_dest),
        }

    async def resize_and_save_resized_image(
        self,
        height: int,
        image: Any,
        timestamp: str | None,
        upload_dir: Path,
        upload_file,
        _type: str,
    ):
        self.logger.debug("Start resizing image")
        filename = f"{timestamp}_{_type}_{upload_file.filename}"
        self.logger.debug(f"Icon filename: {filename}")
        dest = upload_dir / filename
        try:
            width = int((image.width / image.height) * height)
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            await self.save_file_with_image_format_to_destination(
                dest, resized_image, image
            )
            self.logger.info(f"Resized image {filename} saved to {dest}")
            return filename
        except Exception as e:
            self.logger.error(f"Problem resizing image: {e}")

    async def save_file_with_image_format_to_destination(self, dest, save_image, image):
        self.logger.debug(f"Saving image for subfolder: {dest}")
        try:
            with dest.open("wb") as icon_buffer:
                save_image.save(icon_buffer, format=image.format)
            self.logger.info(f"Image saved: {dest}")
        except Exception as e:
            self.logger.error(f"Problem saving image to: {save_image} {e}")
            raise HTTPException(
                status_code=400, detail="An error occurred while saving file."
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
        img = Image.open(image_path)

        # If the image has an alpha (transparency) channel, convert it to RGB
        if img.mode == "RGBA":
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

    async def download_image(self, img_url: str, image_path: str) -> str:
        self.logger.debug(f"Downloading image from {img_url} to {image_path}")
        try:
            image_data = await self.fetch_image_data_from_url(img_url)
            await self.ensure_directory_created(image_path)
            await self.save_image_to_file(image_data, image_path)
            return image_path
        except Exception as e:
            self.logger.error(
                f"Error downloading image from {img_url} to {image_path}: {e}"
            )
            raise

    # async def download_image(self, img_url: str, image_path: str):
    #     self.logger.debug(f"Downloading image from {img_url} to {image_path}")
    #     try:
    #         async with ClientSession() as session:
    #             async with session.get(img_url) as response:
    #                 self.logger.debug(f"Got response: {response}")
    #                 if response.status != 200:
    #                     self.logger.info(f"Response status code: {response.status}")
    #                     response.raise_for_status()
    #                 try:
    #                     image_data = await response.read()
    #                     self.logger.debug(f"Got image data: {image_data}")
    #                 except Exception as e:
    #                     self.logger.error(
    #                         f"Problem with reading image data {image_data} {e}"
    #                     )
    #
    #                 try:
    #                     self.logger.debug(f"Try creating directory {image_path}")
    #                     os.makedirs(os.path.dirname(image_path), exist_ok=True)
    #                     self.logger.debug(
    #                         f"Directory created successfully {image_path}"
    #                     )
    #                 except Exception as e:
    #                     self.logger.error(
    #                         f"Problem creating directory {image_path} {e}"
    #                     )
    #                 try:
    #                     self.logger.debug(f"Open file path: {image_path}")
    #                     with open(image_path, "wb") as fp:
    #                         self.logger.debug(f"Writing image to file {image_path}")
    #                         fp.write(image_data)
    #                         self.logger.info(f"Image saved: {image_path}")
    #                         return image_path
    #                 except Exception as e:
    #                     self.logger.error(
    #                         f"Problem writing image data to {image_path} {e}"
    #                     )
    #     except Exception as e:
    #         self.logger.error(
    #             f"Problem with downloading from {img_url} to {image_path} {e}"
    #         )

    async def open_file_from_path(self, image_path: str) -> Image:
        try:
            self.logger.debug(f"Opening image from {image_path}")
            with open(image_path, "rb") as file:
                image_data = file.read()
                return image_data
        except Exception as e:
            self.logger.error(f"Error opening image from {image_path}: {e}")
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
        original_image_path: str,
        icon_image_path: str,
        web_view_image_path: str,
        icon_height: int = 100,
        web_view_height: int = 400,
    ):
        self.logger.debug(f"Initialize download and resize image from {img_url}")
        image_path = await self.download_image(img_url, original_image_path)
        file = await self.open_file_from_path(image_path)
        image = await self.open_image_from_file(file)

        created_icon_path = await self.create_path(icon_image_path)
        await self.resize_and_save_resized_image(
            icon_height, image, None, Path(created_icon_path), file, "icon"
        )

        created_web_view_path = await self.create_path(web_view_image_path)
        await self.resize_and_save_resized_image(
            web_view_height, image, None, Path(created_web_view_path), file, "webview"
        )

        # async with ClientSession() as session:
        #     async with session.get(img_url) as response:
        #         if response.status != 200:
        #             response.raise_for_status()
        #         image_data = await response.read()
        #
        #         # Save the original image
        #         os.makedirs(os.path.dirname(original_image_path), exist_ok=True)
        #         with open(original_image_path, "wb") as original_fp:
        #             original_fp.write(image_data)
        #         image = Image.open(BytesIO(image_data))
        #
        #         # Create and save the icon image
        #         icon_width = int((image.width / image.height) * icon_height)
        #         icon_image = image.resize(
        #             (icon_width, icon_height), Image.Resampling.LANCZOS
        #         )
        #         os.makedirs(os.path.dirname(icon_image_path), exist_ok=True)
        #         with open(icon_image_path, "wb") as icon_fp:
        #             image_format = "PNG" if image.format is None else image.format
        #             icon_image.save(icon_fp, format=image_format)
        #
        #         # Create and save the web view image
        #         web_view_width = int((image.width / image.height) * web_view_height)
        #         web_view_image = image.resize(
        #             (web_view_width, web_view_height), Image.Resampling.LANCZOS
        #         )
        #         os.makedirs(os.path.dirname(web_view_image_path), exist_ok=True)
        #         with open(web_view_image_path, "wb") as web_fp:
        #             image_format = "PNG" if image.format is None else image.format
        #             web_view_image.save(web_fp, format=image_format)

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
            return path
        except Exception as e:
            self.logger.error(f"Error creating path {path}: {e}")
            raise

    # Import necessary modules at the top (os, urlparse, etc.)

    async def download_and_process_image(
        self,
        image_url: str,
        image_type_prefix: str,
        image_title: str,
        icon_height: int,
        web_view_height: int,
    ):
        path = urlparse(image_url).path
        ext = Path(path).suffix

        main_path = f"{image_type_prefix}"
        static_uploads_path = "/static/uploads/"

        image_filename = image_title.strip().replace(" ", "_")
        image_icon_filename = f"{image_filename}_{icon_height}px{ext}"
        image_webview_filename = f"{image_filename}_{web_view_height}px{ext}"

        image_path = os.path.join(uploads_path, f"{main_path}{image_filename}{ext}")
        image_icon_path = os.path.join(
            uploads_path, f"{main_path}{image_icon_filename}"
        )
        image_webview_path = os.path.join(
            uploads_path, f"{main_path}{image_webview_filename}"
        )

        relative_image_path = os.path.join(
            f"{static_uploads_path}{main_path}", f"{image_filename}{ext}"
        )
        relative_image_icon_path = os.path.join(
            f"{static_uploads_path}{main_path}", f"{image_icon_filename}"
        )
        relative_image_webview_path = os.path.join(
            f"{static_uploads_path}{main_path}", f"{image_webview_filename}"
        )

        # Download and resize the image
        await file_service.download_and_resize_image(
            image_url,
            image_path,
            image_icon_path,
            image_webview_path,
            icon_height=icon_height,
            web_view_height=web_view_height,
        )

        # Return the relative paths for use in the data structure
        return {
            "image_path": image_path,
            "image_url": relative_image_path,
            "image_icon_url": relative_image_icon_path,
            "image_webview_url": relative_image_webview_path,
        }

    @staticmethod
    def hex_to_rgb(hex_color: str):
        hex_color = hex_color.lstrip("#")
        # Convert the hex color to a tuple of integers and return it.
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


file_service = FileService()
