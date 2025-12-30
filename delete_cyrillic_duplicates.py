#!/usr/bin/env python3
"""Script to delete Cyrillic image files when Latin versions exist."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.helpers.text_helpers import convert_cyrillic_filename

def cleanup_cyrillic_duplicates(directory: str, dry_run: bool = True):
    """Delete Cyrillic files when Latin versions exist."""
    deleted_count = 0
    error_count = 0

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories
        if not os.path.isfile(filepath):
            continue
        
        # Check if filename contains non-ASCII (Cyrillic)
        try:
            filename.encode('ascii')
            continue  # Filename is already ASCII
        except UnicodeEncodeError:
            pass
        
        # Get converted filename
        converted_filename = convert_cyrillic_filename(filename)
        
        if converted_filename == filename:
            continue
            
        converted_filepath = os.path.join(directory, converted_filename)
        
        # Check if converted filename exists
        if not os.path.exists(converted_filepath):
            print(f"WARNING: No Latin version found for: {filename}")
            error_count += 1
            continue
        
        if dry_run:
            print(f"[DRY RUN] Would delete Cyrillic duplicate:")
            print(f"  {filename}")
            print(f"  (keeping: {converted_filename})")
        else:
            try:
                os.remove(filepath)
                print(f"Deleted: {filename}")
                print(f"  (keeping: {converted_filename})")
                deleted_count += 1
            except Exception as e:
                print(f"ERROR deleting {filename}: {e}")
                error_count += 1
    
    print(f"\n{'=' * 60}")
    if dry_run:
        print(f"DRY RUN COMPLETE - {deleted_count} files would be deleted")
    else:
        print(f"COMPLETE - {deleted_count} files deleted, {error_count} errors")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    uploads_dir = "static/uploads/persons/photos"
    
    if not os.path.exists(uploads_dir):
        print(f"Directory does not exist: {uploads_dir}")
        sys.exit(1)
    
    print("Checking for Cyrillic duplicate files in:", uploads_dir)
    print("=" * 60)
    
    # First do a dry run
    cleanup_cyrillic_duplicates(uploads_dir, dry_run=True)
    
    # Ask user to proceed
    response = input("\nProceed with deletion? (yes/no): ").strip().lower()
    if response in ['yes', 'y']:
        cleanup_cyrillic_duplicates(uploads_dir, dry_run=False)
    else:
        print("Aborted.")
