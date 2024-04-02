import os
import shutil
from PIL import Image
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
