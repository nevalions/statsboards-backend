from datetime import datetime

from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil


class FileService:

    def __init__(
            self,
            upload_dir: Path = Path('/home/linroot/code/statsboards/statsboards-angular-legacy/src/assets/uploads'),
    ):
        self.base_upload_dir = upload_dir
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_image(self, upload_file: UploadFile, sub_folder: str):
        print('Saving image...')

        upload_dir = self.base_upload_dir / sub_folder
        upload_dir.mkdir(parents=True, exist_ok=True)

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
        rel_dest = Path('/assets/uploads') / sub_folder / filename
        return str(rel_dest)


file_service = FileService()

# async def save_upload_file(self, upload_file: UploadFile):
#     try:
#         dest = self.upload_dir / upload_file.filename
#
#         if upload_file.content_type.startswith('image/'):
#             # perform image-specific processing here, e.g., resizing, format conversion
#             pass
#
#         elif upload_file.content_type == 'text/csv':
#             # perform CSV-specific processing here, e.g., parse and validate CSV data
#             pass
#
#         elif upload_file.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
#             pass
#             # perform Excel-specific processing here, e.g., convert to CSV
#
#             # Load the workbook
#             # workbook = load_workbook(upload_file.file)
#
#             # You can now access the worksheets, rows and cells for further processing
#             # Make sure to implement this according to your actual requirements
#
#         elif upload_file.content_type == 'text/plain':
#             # process text files here if required
#             pass
#
#         # Note: Add necessary clauses to handle additional file types as required
#
#         else:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Unsupported file type",
#             )
#
#         with dest.open("wb") as buffer:
#             shutil.copyfileobj(upload_file.file, buffer)
#
#         return dest
#
#     except Exception as ex:
#         print(ex)
#         raise HTTPException(
#             status_code=400,
#             detail="An error occurred while uploading file.",
#         )
