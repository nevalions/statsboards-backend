#!/usr/bin/env python3
"""Script to rename Cyrillic image filenames to Latin alphabet."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.helpers.text_helpers import convert_cyrillic_filename


def rename_cyrillic_files(directory: str, dry_run: bool = True):
    """Rename files with Cyrillic characters to Latin alphabet."""
    renamed_count = 0
    error_count = 0

    dir_path = Path(directory)

    for filepath in dir_path.iterdir():
        # Skip directories
        if not filepath.is_file():
            continue

        filename = filepath.name

        # Check if filename contains Cyrillic characters
        try:
            filename.encode("ascii")
            continue  # Filename is already ASCII
        except UnicodeEncodeError:
            # Filename contains non-ASCII characters (Cyrillic)
            pass

        # Convert filename to Latin
        converted_filename = convert_cyrillic_filename(filename)

        if converted_filename == filename:
            print(f"No conversion needed for: {filename}")
            continue

        converted_filepath = dir_path / converted_filename

        # Check if converted filename already exists
        if converted_filepath.exists():
            print(f"WARNING: Converted filename already exists: {converted_filename}")
            print(f"  Skipping: {filename}")
            error_count += 1
            continue

        if dry_run:
            print("[DRY RUN] Would rename:")
            print(f"  {filename} -> {converted_filename}")
        else:
            try:
                filepath.rename(converted_filepath)
                print(f"Renamed: {filename} -> {converted_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"ERROR renaming {filename}: {e}")
                error_count += 1

    print(f"\n{'=' * 60}")
    if dry_run:
        print(f"DRY RUN COMPLETE - {renamed_count} files would be renamed")
    else:
        print(f"COMPLETE - {renamed_count} files renamed, {error_count} errors")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    uploads_dir = Path("static/uploads/persons/photos")

    if not uploads_dir.exists():
        print(f"Directory does not exist: {uploads_dir}")
        sys.exit(1)

    print("Checking for Cyrillic filenames in:", uploads_dir)
    print("=" * 60)

    # First do a dry run
    rename_cyrillic_files(str(uploads_dir), dry_run=True)

    # Ask user to proceed
    response = input("\nProceed with actual renaming? (yes/no): ").strip().lower()
    if response in ["yes", "y"]:
        rename_cyrillic_files(str(uploads_dir), dry_run=False)
    else:
        print("Aborted.")
