from io import BytesIO
from pathlib import Path

from fastapi import HTTPException
from PIL import Image

from src.logging_config import get_logger


class ImageProcessingService:
    def __init__(self):
        self.logger = get_logger("backend_logger_imageprocessing", self)

    async def open_image_from_file(self, file_data: bytes) -> Image.Image:
        try:
            self.logger.debug("Opening image from file data")
            image = Image.open(BytesIO(file_data))
            return image
        except Exception as e:
            self.logger.error(f"Error opening image from file: {e}", exc_info=True)
            raise

    async def open_image_from_path(self, image_path: str) -> Image.Image:
        try:
            self.logger.debug(f"Opening image from {image_path}")
            with open(image_path, "rb") as file:
                image_data = file.read()
                return Image.open(BytesIO(image_data))
        except Exception as e:
            self.logger.error(
                f"Error opening image from {image_path}: {e}", exc_info=True
            )
            raise

    async def save_image(
        self, dest: Path, save_image: Image.Image, source_image: Image.Image
    ) -> None:
        self.logger.debug(f"Saving image to folder: {dest}")
        try:
            with dest.open("wb") as buffer:
                save_image.save(buffer, format=source_image.format)
            self.logger.info(f"Image saved: {dest}")
        except Exception as e:
            self.logger.error(f"Problem saving image to: {dest} {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail="An error occurred while saving image.",
            )

    async def resize_image(self, image: Image.Image, height: int) -> Image.Image:
        try:
            width = int((image.width / image.height) * height)
        except Exception as e:
            self.logger.error(f"Problem getting width: {e}", exc_info=True)
            raise

        try:
            resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
            return resized_image
        except Exception as e:
            self.logger.error(f"Problem resizing image: {e}", exc_info=True)
            raise

    async def resize_and_save(
        self,
        dest: Path,
        file_name: str,
        height: int,
        image: Image.Image,
    ) -> None:
        resized_image = await self.resize_image(image, height)
        await self.save_image(dest, resized_image, image)
        self.logger.info(f"Resized image {file_name} saved to {dest}")

    async def generate_filename(
        self,
        _type: str | None,
        file_name: str,
        timestamp: str | None,
        upload_file_filename: str | None,
    ) -> str:
        self.logger.debug(f"Generating filename: {file_name}")
        if upload_file_filename:
            file_name = upload_file_filename
        if timestamp and upload_file_filename:
            file_name = f"{timestamp}_{upload_file_filename}"
        if timestamp and _type and upload_file_filename:
            file_name = f"{timestamp}_{_type}_{upload_file_filename}"
        self.logger.debug(f"Generated filename: {file_name}")
        return file_name

    async def resize_and_save_image(
        self,
        height: int,
        image: Image.Image,
        timestamp: str | None,
        upload_dir: Path,
        upload_file_filename: str,
        _type: str,
    ) -> str:
        self.logger.debug(f"Start resizing {_type} image")
        file_name = await self.generate_filename(
            _type, "resized_img", timestamp, upload_file_filename
        )

        self.logger.debug(f"Resized image filename: {file_name}")
        dest = upload_dir / file_name

        try:
            await self.resize_and_save(dest, file_name, height, image)
            return file_name
        except Exception as e:
            self.logger.error(f"Problem resizing image: {e}", exc_info=True)
            raise

    def hex_to_rgb(self, hex_color: str) -> tuple[int, ...] | None:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) not in (6, 8) or not all(
            c in "0123456789abcdefABCDEF" for c in hex_color
        ):
            return None
        try:
            self.logger.debug(f"Converting hex color: {hex_color}")
            final_color = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            self.logger.info(f"Converted hex color: {final_color}")
            return final_color
        except Exception as e:
            self.logger.warning(f"Problem converting hex color: {hex_color} {e}")
            return None

    async def get_most_common_color(self, image_path: str) -> str | None:
        self.logger.debug(f"Getting most common color: {image_path}")
        img = Image.open(image_path)

        if img.mode == "RGBA":
            self.logger.debug(f"Converting RGBA to RGB: {img.mode}")
            temp_img = Image.new("RGB", img.size)
            temp_img.paste(img, mask=img.split()[3])
            img_rgb = temp_img
        else:
            img_rgb = img

        colors = img_rgb.convert("RGB").getcolors(img_rgb.size[0] * img_rgb.size[1])

        if colors and isinstance(colors, list):
            colors.sort(key=lambda tup: tup[0], reverse=True)

            excluded_colors = [
                (0,),
                (255,),
                (254,),
                self.hex_to_rgb("#000105") or (),
                self.hex_to_rgb("#fdfdfd") or (),
                self.hex_to_rgb("#dfdfdf") or (),
                self.hex_to_rgb("#fcfcfc") or (),
            ]

            most_common_color = next(
                (color for count, color in colors if color not in excluded_colors),
                None,
            )

            if most_common_color:
                return "#{:02x}{:02x}{:02x}".format(*most_common_color)
            else:
                return None
        else:
            self.logger.warning("No common color detected")
            return None
