from pathlib import Path

from src.core.config import uploads_path


def photo_files_exist(person_photo_url: str | None) -> bool:
    """Check if photo files exist on disk and have valid size."""
    if not person_photo_url:
        return False

    try:
        photo_filename = Path(person_photo_url).name
        if photo_filename:
            original_path = Path(uploads_path) / "persons" / "photos" / photo_filename
            icon_path = (
                original_path.parent
                / f"{Path(photo_filename).stem}_100px{Path(photo_filename).suffix}"
            )
            web_path = (
                original_path.parent
                / f"{Path(photo_filename).stem}_400px{Path(photo_filename).suffix}"
            )

            min_file_size = 1024

            for path in [original_path, icon_path, web_path]:
                if path.exists():
                    file_size = path.stat().st_size
                    if file_size >= min_file_size:
                        return True

            return False
    except (OSError, ValueError, AttributeError):
        pass

    return False
