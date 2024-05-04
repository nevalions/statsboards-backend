import os
import shutil
from src.core.config import uploads_path
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO
from aiohttp import ClientSession
from datetime import datetime
from fastapi import UploadFile, HTTPException
from pathlib import Path


class FileService:

    def __init__(
            self,
            upload_dir: Path = Path(__file__).resolve().parent.parent.parent / 'static/uploads',
    ):
        self.base_upload_dir = upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(sels, filename):
        filename = filename.strip().replace(' ', '_')

        return filename

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str):
        print('Saving image...')

        upload_dir = self.base_upload_dir / sub_folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(upload_dir)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{upload_file.filename}"

        dest = upload_dir / filename

        if not upload_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        try:
            with dest.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as ex:
            print(ex)
            raise HTTPException(status_code=400, detail="An error occurred while uploading file.")

        print('file destination', str(dest))

        # Construct the relative path
        rel_dest = Path('/static/uploads') / sub_folder / filename
        return str(rel_dest)

    async def save_and_resize_upload_image(
            self,
            upload_file: UploadFile,
            sub_folder: str,
            icon_height: int = 100,
            web_view_height: int = 400,
    ):
        print('Saving image...')

        upload_dir = self.base_upload_dir / sub_folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(upload_dir)

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        original_filename = f"{timestamp}_{upload_file.filename}"
        original_dest = upload_dir / original_filename

        if not upload_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        try:
            with original_dest.open("wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as ex:
            print(ex)
            raise HTTPException(status_code=400, detail="An error occurred while uploading file.")

        print('Original file destination', str(original_dest))

        # Open the image for resizing
        with original_dest.open("rb") as image_file:
            image = Image.open(image_file)

            # Create and save the icon image
            icon_filename = f"{timestamp}_icon_{upload_file.filename}"
            icon_dest = upload_dir / icon_filename
            icon_width = int((image.width / image.height) * icon_height)
            icon_image = image.resize((icon_width, icon_height), Image.Resampling.LANCZOS)

            with icon_dest.open("wb") as icon_buffer:
                icon_image.save(icon_buffer, format=image.format)

            # Create and save the web view image
            webview_filename = f"{timestamp}_webview_{upload_file.filename}"
            webview_dest = upload_dir / webview_filename
            webview_width = int((image.width / image.height) * web_view_height)
            webview_image = image.resize((webview_width, web_view_height), Image.Resampling.LANCZOS)

            with webview_dest.open("wb") as webview_buffer:
                webview_image.save(webview_buffer, format=image.format)

        # Construct relative path for all images
        rel_original_dest = Path('/static/uploads') / sub_folder / original_filename
        rel_icon_dest = Path('/static/uploads') / sub_folder / icon_filename
        rel_webview_dest = Path('/static/uploads') / sub_folder / webview_filename

        # Create a dictionary to return the paths of all the image versions created
        return {
            "original": str(rel_original_dest),
            "icon": str(rel_icon_dest),
            "webview": str(rel_webview_dest)
        }

    async def get_most_common_color(self, image_path: str):
        img = Image.open(image_path)

        # If the image has an alpha (transparency) channel, convert it to RGB
        if img.mode == 'RGBA':
            temp_img = Image.new("RGB", img.size)
            temp_img.paste(img, mask=img.split()[3])  # 3 is the alpha channel
            img = temp_img

        colors = img.convert('RGB').getcolors(img.size[0] * img.size[1])  # Ensures RGB data
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
            most_common_color = next((color for count, color in colors if set(color) not in excluded_colors), None)
            return '#{:02x}{:02x}{:02x}'.format(*most_common_color) if most_common_color else None
        else:
            return None

    async def download_image(self, img_url: str, image_path: str):
        async with ClientSession() as session:
            async with session.get(img_url) as response:
                if response.status != 200:
                    response.raise_for_status()
                image_data = await response.read()

                # Ensure the destination directory exists
                os.makedirs(os.path.dirname(image_path), exist_ok=True)

                # Write image data to file
                with open(image_path, 'wb') as fp:
                    fp.write(image_data)

    async def download_and_resize_image(
            self,
            img_url: str,
            original_image_path: str,
            icon_image_path: str,
            web_view_image_path: str,
            icon_height: int = 100,
            web_view_height: int = 400,

    ):
        async with ClientSession() as session:
            async with session.get(img_url) as response:
                if response.status != 200:
                    response.raise_for_status()
                image_data = await response.read()

                # Save the original image
                os.makedirs(os.path.dirname(original_image_path), exist_ok=True)
                with open(original_image_path, 'wb') as original_fp:
                    original_fp.write(image_data)

                image = Image.open(BytesIO(image_data))

                # Create and save the icon image
                icon_width = int((image.width / image.height) * icon_height)
                icon_image = image.resize((icon_width, icon_height), Image.Resampling.LANCZOS)
                os.makedirs(os.path.dirname(icon_image_path), exist_ok=True)
                with open(icon_image_path, 'wb') as icon_fp:
                    image_format = 'PNG' if image.format is None else image.format
                    icon_image.save(icon_fp, format=image_format)

                # Create and save the web view image
                web_view_width = int((image.width / image.height) * web_view_height)
                web_view_image = image.resize((web_view_width, web_view_height), Image.Resampling.LANCZOS)
                os.makedirs(os.path.dirname(web_view_image_path), exist_ok=True)
                with open(web_view_image_path, 'wb') as web_fp:
                    web_view_image.save(web_fp, format=image_format)

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
        image_icon_path = os.path.join(uploads_path, f"{main_path}{image_icon_filename}")
        image_webview_path = os.path.join(uploads_path, f"{main_path}{image_webview_filename}")

        relative_image_path = os.path.join(
            f"{static_uploads_path}{main_path}",
            f"{image_filename}{ext}"
        )
        relative_image_icon_path = os.path.join(
            f"{static_uploads_path}{main_path}",
            f"{image_icon_filename}"
        )
        relative_image_webview_path = os.path.join(
            f"{static_uploads_path}{main_path}",
            f"{image_webview_filename}"
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

    def hex_to_rgb(self, hex_color: str):
        hex_color = hex_color.lstrip('#')
        # Convert the hex color to a tuple of integers and return it.
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    # async def download_image(self, img_url: str, image_path: str):
    #     response = requests.get(img_url)
    #     response.raise_for_status()  # Raise an exception for HTTP errors
    #
    #     # Ensure the destination directory exists
    #     os.makedirs(os.path.dirname(image_path), exist_ok=True)
    #
    #     with open(image_path, 'wb') as fp:
    #         fp.write(response.content)


file_service = FileService()
