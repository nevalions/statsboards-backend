import shutil
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from fastapi import HTTPException, UploadFile

from src.helpers.file_system_service import FileSystemService
from src.helpers.text_helpers import convert_cyrillic_filename
from src.logging_config import get_logger


class ImageData(TypedDict):
    dest: Path
    filename: str
    timestamp: str
    upload_dir: Path


class UploadService:
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self, fs_service: FileSystemService):
        self.fs_service = fs_service
        self.logger = get_logger("upload", self)

    async def validate_file_size(self, upload_file: UploadFile) -> None:
        upload_file.file.seek(0, 2)  # Seek to end
        size = upload_file.file.tell()
        upload_file.file.seek(0)  # Reset

        if size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {self.MAX_FILE_SIZE} bytes",
            )

    async def sanitize_filename(self, filename: str) -> str:
        self.logger.debug(f"Sanitizing filename: {filename}")
        try:
            import re
            import unicodedata

            normalized = unicodedata.normalize("NFKD", filename)
            ascii_only = normalized.encode("ASCII", "ignore").decode("ASCII")
            sanitized = Path(ascii_only).name.strip().replace(" ", "_")
            sanitized = sanitized.replace("\x00", "")
            sanitized = re.sub(r"[^\w\-_\.]", "_", sanitized)
            self.logger.debug(f"Sanitized filename: {sanitized}")
            return sanitized
        except Exception as e:
            self.logger.error(f"Problem with sanitizing filename: {filename} {e}")
            raise

    async def get_timestamp(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.logger.debug(f"Timestamp: {timestamp}")
        return timestamp

    async def get_filename(self, timestamp: str, upload_file: UploadFile) -> str:
        original_filename = f"{timestamp}_{upload_file.filename}"
        self.logger.debug(f"Original filename: {original_filename}")
        return original_filename

    async def is_image_type(self, upload_file: UploadFile) -> None:
        if not upload_file.content_type or not upload_file.content_type.startswith("image/"):
            self.logger.error("Uploaded file type not an image", exc_info=True)
            raise HTTPException(status_code=400, detail="Unsupported file type")

    async def upload_file(self, dest: Path, upload_file: UploadFile) -> None:
        try:
            with dest.open("wb") as buffer:
                self.logger.debug("Trying to save file")
                shutil.copyfileobj(upload_file.file, buffer)
        except Exception as ex:
            self.logger.error(
                f"Problem with saving file to destination {dest} {ex}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=400, detail="An error occurred while uploading file."
            ) from ex

    async def upload_image_and_return_data(
        self, sub_folder: str, upload_file: UploadFile
    ) -> ImageData:
        await self.validate_file_size(upload_file)
        upload_dir = await self.fs_service.get_and_create_upload_dir(sub_folder)
        timestamp = await self.get_timestamp()
        unsanitized_filename = await self.get_filename(timestamp, upload_file)
        converted_filename = convert_cyrillic_filename(unsanitized_filename)
        original_filename = await self.sanitize_filename(converted_filename)
        original_dest = await self.fs_service.get_destination_with_filename(
            original_filename, upload_dir
        )
        await self.is_image_type(upload_file)
        await self.upload_file(original_dest, upload_file)
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

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str) -> str:
        self.logger.debug(f"Saving image for subfolder: {sub_folder}")
        data = await self.upload_image_and_return_data(sub_folder, upload_file)
        rel_dest = Path("/static/uploads") / sub_folder / data["filename"]
        self.logger.debug(f"Relative destination path: {rel_dest}")
        return str(rel_dest)
