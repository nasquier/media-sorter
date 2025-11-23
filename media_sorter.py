#!/usr/bin/env python3
"""
Media Sorter - Rename folders with date and title formatting.

This script takes a folder path as input and renames folders to follow
the format: {YYYYMMDD}_{title} where the title is lowercased with dashes
instead of spaces.
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ExifTags

# Supported media file extensions
MEDIA_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
}


def parse_folder_name(folder_name):
    """
    Parse folder name to extract optional date and title.

    Date format: YYYY-MM-DD (month and day are optional)
    Examples:
        - "2023-01-15 My Photos" -> date: "20230115", title: "My Photos"
        - "2023-01 Vacation" -> date: "202301", title: "Vacation"
        - "2023 Summer" -> date: "2023", title: "Summer"
        - "My Photos" -> date: None, title: "My Photos"

    Args:
        folder_name: The original folder name

    Returns:
        tuple: (date_str, title) where date_str is formatted without dashes
               and title is the remaining part
    """
    # Pattern to match optional date at the start
    # YYYY-MM-DD or YYYY-MM or YYYY followed by space and title
    # This pattern requires either a dash or a space after the year to avoid
    # matching already formatted dates like "20230115_my-photos"
    pattern = r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:\s+(.*))?$"
    match = re.match(pattern, folder_name)

    if match:
        year, month, day, title = match.groups()
        # Only treat as a date if there's a dash or space after the year
        # This means "2023-01-15", "2023-01", "2023 Summer" are dates
        # but "20230115_my-photos" is not
        # We check for dash in the date portion (max length YYYY-MM-DD is 10)
        MAX_DATE_LENGTH = 10
        has_dash = "-" in folder_name[:MAX_DATE_LENGTH]
        has_space = " " in folder_name

        if has_dash or (has_space and title):
            # Build date string from available components
            date_str = year
            if month:
                date_str += month
            if day:
                date_str += day
            # If no title provided after date, use empty string
            title = title if title else ""
            return date_str, title

    # No valid date found, entire name is title
    return None, folder_name


def format_folder_name(date_str, title):
    """
    Format folder name according to the specification.

    Format: {YYYYMMDD}_{title} where title is lowercased with dashes

    Args:
        date_str: Date string without dashes (e.g., "20230115", "202301", "2023")
        title: Title text

    Returns:
        str: Formatted folder name
    """
    # Convert title to lowercase and replace spaces with dashes
    formatted_title = title.lower().replace(" ", "-")

    if date_str:
        if formatted_title:
            return f"{date_str}_{formatted_title}"
        else:
            return date_str
    else:
        # If no date, return formatted title (always lowercase with dashes)
        return formatted_title


def should_rename(original_name, new_name):
    """
    Check if a folder should be renamed.

    Args:
        original_name: Original folder name
        new_name: Proposed new folder name

    Returns:
        bool: True if renaming is needed
    """
    return original_name != new_name


def extract_title_from_folder_name(folder_name):
    """
    Extract just the title portion from a folder name, removing any date prefix.

    Handles both formatted (YYYYMMDD_title) and unformatted (YYYY-MM-DD Title) names.

    Args:
        folder_name: The folder name to extract title from

    Returns:
        str: The title portion of the folder name
    """
    # Check if it's already in formatted form: YYYYMMDD_title or YYYYMM_title or YYYY_title
    formatted_pattern = r"^(\d{4,8})_(.+)$"
    match = re.match(formatted_pattern, folder_name)
    if match:
        _, title = match.groups()
        return title

    # Otherwise, try to parse as unformatted date
    date_str, title = parse_folder_name(folder_name)
    if date_str and title:
        # Has a date and title, return just the title
        return title
    elif not date_str and title:
        # No date, entire name is the title
        return title
    else:
        # Edge case: date but no title (shouldn't happen in practice)
        return folder_name


def get_media_file_datetime(file_path):
    """
    Extract datetime from media file EXIF metadata.

    Args:
        file_path: Path to the media file

    Returns:
        datetime object if metadata exists, None otherwise
    """
    try:
        with Image.open(file_path) as image:
            exif_data = image.getexif()

            if exif_data is not None and len(exif_data) > 0:
                # Try multiple datetime tags in order of preference
                # DateTimeOriginal: when photo was taken
                # DateTimeDigitized: when photo was digitized
                # DateTime: when file was last modified
                datetime_tags = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]

                for preferred_tag in datetime_tags:
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag == preferred_tag:
                            # Parse the datetime string (format: "YYYY:MM:DD HH:MM:SS")
                            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            return dt
        return None
    except Exception:
        # If file can't be opened or doesn't have EXIF data (e.g., videos)
        return None


def generate_unique_filename(directory, base_name, extension):
    """
    Generate a unique filename in the directory by adding a counter if needed.

    Args:
        directory: Path object for the directory
        base_name: Base name for the file (without extension)
        extension: File extension (including the dot)

    Returns:
        str: Unique filename
    """
    # Try the base name first
    candidate = f"{base_name}{extension}"
    candidate_path = directory / candidate

    if not candidate_path.exists():
        return candidate

    # File exists, start adding counters
    counter = 1
    while True:
        candidate = f"{base_name}_{counter:03d}{extension}"
        candidate_path = directory / candidate

        if not candidate_path.exists():
            return candidate

        counter += 1
        if counter > 999:
            # Safety limit
            raise ValueError(f"Too many files with base name {base_name}")


def rename_media_file(file_path, parent_dir_name):
    """
    Rename a media file based on its metadata or parent directory name.

    Args:
        file_path: Path to the media file
        parent_dir_name: Name of the parent directory

    Returns:
        tuple: (old_path, new_path) if renamed, None if not renamed
    """
    file_path = Path(file_path)

    # Get file extension
    extension = file_path.suffix.lower()

    if extension not in MEDIA_EXTENSIONS:
        return None

    # Try to extract datetime from metadata
    dt = get_media_file_datetime(file_path)

    if dt:
        # Format: YYYYMMDDHHMMSS_title.ext (title only, no date prefix)
        title = extract_title_from_folder_name(parent_dir_name)
        base_name = f"{dt.strftime('%Y%m%d%H%M%S')}_{title}"
    else:
        # No metadata, use parent directory name
        base_name = parent_dir_name

    # Generate unique filename
    new_filename = generate_unique_filename(file_path.parent, base_name, extension)
    new_path = file_path.parent / new_filename

    # Check if renaming is needed
    if file_path.name != new_filename:
        try:
            file_path.rename(new_path)
            return (str(file_path), str(new_path))
        except Exception as e:
            print(f"Error renaming {file_path} to {new_path}: {e}")
            return None

    return None


def rename_folders(root_path):
    """
    Recursively rename folders and media files in the directory tree from top to bottom.

    Args:
        root_path: Root directory path to start processing

    Returns:
        dict: Dictionary with 'folders' and 'files' keys containing lists of renamed items
    """
    root_path = Path(root_path).resolve()

    if not root_path.exists():
        raise ValueError(f"Path does not exist: {root_path}")

    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_path}")

    renamed_folders = []
    renamed_files = []

    # Walk the directory tree from top to bottom
    # We need to process in sorted order to ensure consistent behavior
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Sort dirnames to process in consistent order
        dirnames.sort()
        filenames.sort()

        # Process each subdirectory
        dirs_to_rename = []
        for dirname in dirnames:
            old_path = Path(dirpath) / dirname

            # Parse the folder name
            date_str, title = parse_folder_name(dirname)

            # Format the new folder name
            new_name = format_folder_name(date_str, title)

            # Check if renaming is needed
            if should_rename(dirname, new_name):
                new_path = Path(dirpath) / new_name
                dirs_to_rename.append((old_path, new_path, dirname, new_name))

        # Perform folder renames (we do this after collecting to avoid issues with iteration)
        for old_path, new_path, old_name, new_name in dirs_to_rename:
            try:
                old_path.rename(new_path)
                renamed_folders.append((str(old_path), str(new_path)))
                print(f"Renamed folder: {old_path} -> {new_path}")

                # Update dirnames list to reflect the rename
                idx = dirnames.index(old_name)
                dirnames[idx] = new_name
            except Exception as e:
                print(f"Error renaming {old_path} to {new_path}: {e}")

        # Process media files in the current directory
        # Get the current directory name for use in file renaming
        current_dir_name = Path(dirpath).name

        for filename in filenames:
            file_path = Path(dirpath) / filename
            result = rename_media_file(file_path, current_dir_name)
            if result:
                renamed_files.append(result)
                print(f"Renamed file: {result[0]} -> {result[1]}")

    return {"folders": renamed_folders, "files": renamed_files}


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Rename folders and media files with date and title formatting."
    )
    parser.add_argument("folder_path", help="Path to the folder to process")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming",
    )

    args = parser.parse_args()

    try:
        if args.dry_run:
            # For dry run, we'll walk the tree and show what would be renamed
            root_path = Path(args.folder_path).resolve()
            if not root_path.exists():
                print(f"Error: Path does not exist: {root_path}")
                return 1

            print("Dry run - no actual changes will be made:")
            folder_count = 0
            file_count = 0

            for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
                dirnames.sort()
                filenames.sort()

                # Check folders
                for dirname in dirnames:
                    date_str, title = parse_folder_name(dirname)
                    new_name = format_folder_name(date_str, title)
                    if should_rename(dirname, new_name):
                        old_path = Path(dirpath) / dirname
                        new_path = Path(dirpath) / new_name
                        print(f"Would rename folder: {old_path} -> {new_path}")
                        folder_count += 1

                # Check files
                current_dir_name = Path(dirpath).name
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    extension = file_path.suffix.lower()

                    if extension in MEDIA_EXTENSIONS:
                        dt = get_media_file_datetime(file_path)
                        if dt:
                            title = extract_title_from_folder_name(current_dir_name)
                            base_name = f"{dt.strftime('%Y%m%d%H%M%S')}_{title}"
                        else:
                            base_name = current_dir_name

                        new_filename = generate_unique_filename(
                            file_path.parent, base_name, extension
                        )
                        if filename != new_filename:
                            new_path = file_path.parent / new_filename
                            print(f"Would rename file: {file_path} -> {new_path}")
                            file_count += 1

            print(f"\nTotal folders that would be renamed: {folder_count}")
            print(f"Total files that would be renamed: {file_count}")
        else:
            result = rename_folders(args.folder_path)
            print(f"\nTotal folders renamed: {len(result['folders'])}")
            print(f"Total files renamed: {len(result['files'])}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
