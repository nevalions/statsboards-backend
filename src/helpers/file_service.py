from datetime import datetime

from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil


class FileService:

    def __init__(
            self,
            upload_dir: Path = Path(__file__).resolve().parent.parent.parent / 'static/uploads',
    ):
        self.base_upload_dir = upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str):
        print('Saving image...')

        upload_dir = self.base_upload_dir / sub_folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        print(upload_dir)

        # Get the current timestamp and add it to the filename
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


file_service = FileService()
