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
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List
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

# EXIF datetime tags in order of preference
DATETIME_EXIF_TAGS = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]

# Constants
MAX_DATE_LENGTH = 10  # Length of "YYYY-MM-DD"
MAX_FILENAME_COUNTER = 999
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass
class ParsedFolderName:
    """Result of parsing a folder name."""

    date_str: Optional[str]
    title: str


@dataclass
class RenameResult:
    """Result of a rename operation."""

    old_path: str
    new_path: str


@dataclass
class RenameStats:
    """Statistics for rename operations."""

    folders: List[RenameResult]
    files: List[RenameResult]

    def to_dict(self) -> Dict[str, List[Tuple[str, str]]]:
        """Convert to dictionary format for backward compatibility."""
        return {
            "folders": [(r.old_path, r.new_path) for r in self.folders],
            "files": [(r.old_path, r.new_path) for r in self.files],
        }


def _has_date_separator(folder_name: str) -> bool:
    """Check if folder name has date separators (dash or space after year)."""
    has_dash = "-" in folder_name[:MAX_DATE_LENGTH]
    has_space = " " in folder_name
    return has_dash or has_space


def parse_folder_name(folder_name: str) -> Tuple[Optional[str], str]:
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

    if not match:
        return None, folder_name

    year, month, day, title = match.groups()

    # Only treat as a date if there's a dash or space after the year
    # This means "2023-01-15", "2023-01", "2023 Summer" are dates
    # but "20230115_my-photos" is not
    if not _has_date_separator(folder_name):
        return None, folder_name

    # Build date string from available components
    date_str = year
    if month:
        date_str += month
    if day:
        date_str += day

    # If no title provided after date, use empty string
    title = title if title else ""
    return date_str, title


def _format_title(title: str) -> str:
    """Format title to lowercase with dashes instead of spaces."""
    return title.lower().replace(" ", "-")


def format_folder_name(date_str: Optional[str], title: str) -> str:
    """
    Format folder name according to the specification.

    Format: {YYYYMMDD}_{title} where title is lowercased with dashes

    Args:
        date_str: Date string without dashes (e.g., "20230115", "202301", "2023")
        title: Title text

    Returns:
        str: Formatted folder name
    """
    formatted_title = _format_title(title)

    if date_str:
        return f"{date_str}_{formatted_title}" if formatted_title else date_str

    return formatted_title


def should_rename(original_name: str, new_name: str) -> bool:
    """
    Check if a folder should be renamed.

    Args:
        original_name: Original folder name
        new_name: Proposed new folder name

    Returns:
        bool: True if renaming is needed
    """
    return original_name != new_name


def _extract_title_from_formatted(folder_name: str) -> Optional[str]:
    """Extract title from already formatted folder name (YYYYMMDD_title)."""
    formatted_pattern = r"^(\d{4}|\d{6}|\d{8})_(.+)$"
    match = re.match(formatted_pattern, folder_name)
    return match.group(2) if match else None


def extract_title_from_folder_name(folder_name: str) -> str:
    """
    Extract just the title portion from a folder name, removing any date prefix.

    Handles both formatted (YYYYMMDD_title) and unformatted (YYYY-MM-DD Title) names.

    Args:
        folder_name: The folder name to extract title from

    Returns:
        str: The title portion of the folder name
    """
    # Check if it's already in formatted form:
    # YYYYMMDD_title or YYYYMM_title or YYYY_title
    title = _extract_title_from_formatted(folder_name)
    if title:
        return title

    # Otherwise, try to parse as unformatted date
    date_str, title = parse_folder_name(folder_name)

    if date_str and title:
        return title
    elif not date_str and title:
        return title

    # Edge case: date but no title (shouldn't happen in practice)
    return folder_name


def _extract_exif_datetime(image: Image.Image) -> Optional[Tuple[datetime, str]]:
    """
    Extract datetime from image EXIF data.

    Returns:
        Tuple of (datetime object, format string used) or None if no valid datetime found.
        The format string indicates the precision of the original EXIF data.
    """
    exif_data = image.getexif()

    if not exif_data:
        return None

    # All supported datetime formats, from most specific to least specific
    datetime_formats = [
        "%Y:%m:%d %H:%M:%S",  # Standard EXIF: "2023:05:15 14:30:45"
        "%Y:%m:%d %H:%M",  # Date with hour and minute: "2023:05:15 14:30"
        "%Y:%m:%d %H",  # Date with hour: "2023:05:15 14"
        "%Y:%m:%d",  # Date only: "2023:05:15"
        "%Y:%m",  # Year and month: "2023:05"
        "%Y",  # Year only: "2023"
    ]

    for preferred_tag in DATETIME_EXIF_TAGS:
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if tag == preferred_tag:
                for fmt in datetime_formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return (dt, fmt)
                    except (ValueError, TypeError):
                        continue

    return None


def _format_datetime_from_exif(dt: datetime, fmt: str) -> str:
    """
    Format datetime based on the precision of the original EXIF data.

    Args:
        dt: datetime object
        fmt: The format string that was used to parse the EXIF data

    Returns:
        Formatted datetime string with appropriate precision
    """
    # Map format strings to output formats (only include what was present)
    format_map = {
        "%Y:%m:%d %H:%M:%S": "%Y%m%d%H%M%S",  # Full: 20230515143045
        "%Y:%m:%d %H:%M": "%Y%m%d%H%M",  # No seconds: 202305151430
        "%Y:%m:%d %H": "%Y%m%d%H",  # Hour only: 2023051514
        "%Y:%m:%d": "%Y%m%d",  # Date only: 20230515
        "%Y:%m": "%Y%m",  # Year+month: 202305
        "%Y": "%Y",  # Year only: 2023
    }

    output_format = format_map.get(fmt, "%Y%m%d%H%M%S")  # Default to full format
    return dt.strftime(output_format)


def get_media_file_datetime(file_path: Path) -> Optional[Tuple[datetime, str]]:
    """
    Extract datetime from media file EXIF metadata.

    Args:
        file_path: Path to the media file

    Returns:
        Tuple of (datetime object, format string) if metadata exists, None otherwise
    """
    try:
        with Image.open(file_path) as image:
            return _extract_exif_datetime(image)
    except Exception:
        # If file can't be opened or doesn't have EXIF data (e.g., videos)
        return None


def generate_unique_filename(directory: Path, base_name: str, extension: str) -> str:
    """
    Generate a unique filename in the directory by adding a counter if needed.

    Args:
        directory: Path object for the directory
        base_name: Base name for the file (without extension)
        extension: File extension (including the dot)

    Returns:
        str: Unique filename

    Raises:
        ValueError: If too many files with the same base name exist
    """
    # Try the base name first
    candidate = f"{base_name}{extension}"
    if not (directory / candidate).exists():
        return candidate

    # File exists, start adding counters
    for counter in range(1, MAX_FILENAME_COUNTER + 1):
        candidate = f"{base_name}_{counter:03d}{extension}"
        if not (directory / candidate).exists():
            return candidate

    raise ValueError(f"Too many files with base name {base_name}")


def _create_base_filename(
    dt_info: Optional[Tuple[datetime, str]], parent_dir_name: str
) -> str:
    """
    Create base filename from datetime and parent directory name.

    Args:
        dt_info: Tuple of (datetime, format_string) or None
        parent_dir_name: Name of the parent directory

    Returns:
        Base filename without extension
    """
    if dt_info:
        dt, fmt = dt_info
        title = extract_title_from_folder_name(parent_dir_name)
        datetime_str = _format_datetime_from_exif(dt, fmt)
        return f"{datetime_str}_{title}"
    return parent_dir_name


def rename_media_file(
    file_path: Path, parent_dir_name: str
) -> Optional[Tuple[str, str]]:
    """
    Rename a media file based on its metadata or parent directory name.

    Args:
        file_path: Path to the media file
        parent_dir_name: Name of the parent directory

    Returns:
        tuple: (old_path, new_path) if renamed, None if not renamed
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension not in MEDIA_EXTENSIONS:
        return None

    # Try to extract datetime from metadata
    dt_info = get_media_file_datetime(file_path)
    base_name = _create_base_filename(dt_info, parent_dir_name)

    # Generate unique filename
    new_filename = generate_unique_filename(file_path.parent, base_name, extension)
    new_path = file_path.parent / new_filename

    # Check if renaming is needed
    if file_path.name == new_filename:
        return None

    try:
        file_path.rename(new_path)
        return (str(file_path), str(new_path))
    except Exception as e:
        print(f"Error renaming {file_path} to {new_path}: {e}")
        return None


def _process_folders_in_directory(
    dirpath: str, dirnames: List[str]
) -> List[Tuple[Path, Path, str, str]]:
    """Collect folders that need to be renamed in a directory."""
    dirs_to_rename = []

    for dirname in dirnames:
        old_path = Path(dirpath) / dirname
        date_str, title = parse_folder_name(dirname)
        new_name = format_folder_name(date_str, title)

        if should_rename(dirname, new_name):
            new_path = Path(dirpath) / new_name
            dirs_to_rename.append((old_path, new_path, dirname, new_name))

    return dirs_to_rename


def _rename_folders_batch(
    dirs_to_rename: List[Tuple[Path, Path, str, str]], dirnames: List[str]
) -> List[RenameResult]:
    """Perform batch folder renaming and return results."""
    renamed = []

    for old_path, new_path, old_name, new_name in dirs_to_rename:
        try:
            old_path.rename(new_path)
            renamed.append(RenameResult(str(old_path), str(new_path)))
            print(f"Renamed folder: {old_path} -> {new_path}")

            # Update dirnames list to reflect the rename
            idx = dirnames.index(old_name)
            dirnames[idx] = new_name
        except Exception as e:
            print(f"Error renaming {old_path} to {new_path}: {e}")

    return renamed


def _process_files_in_directory(
    dirpath: str, filenames: List[str]
) -> List[RenameResult]:
    """Process and rename media files in a directory."""
    renamed = []
    current_dir_name = Path(dirpath).name

    for filename in filenames:
        file_path = Path(dirpath) / filename
        result = rename_media_file(file_path, current_dir_name)
        if result:
            renamed.append(RenameResult(*result))
            print(f"Renamed file: {result[0]} -> {result[1]}")

    return renamed


def rename_folders(root_path: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Recursively rename folders and media files in the directory tree from top to bottom.

    Args:
        root_path: Root directory path to start processing

    Returns:
        dict: Dictionary with 'folders' and 'files' keys containing lists of renamed
        items

    Raises:
        ValueError: If path doesn't exist or is not a directory
    """
    root_path = Path(root_path).resolve()

    if not root_path.exists():
        raise ValueError(f"Path does not exist: {root_path}")

    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_path}")

    stats = RenameStats(folders=[], files=[])

    # Walk the directory tree from top to bottom
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Sort for consistent behavior
        dirnames.sort()
        filenames.sort()

        # Process folders
        dirs_to_rename = _process_folders_in_directory(dirpath, dirnames)
        renamed_folders = _rename_folders_batch(dirs_to_rename, dirnames)
        stats.folders.extend(renamed_folders)

        # Process files
        renamed_files = _process_files_in_directory(dirpath, filenames)
        stats.files.extend(renamed_files)

    return stats.to_dict()


def _dry_run_folders(root_path: Path) -> Tuple[int, int]:
    """
    Perform dry run to count what would be renamed.

    Args:
        root_path: Root directory path to check

    Returns:
        tuple: (folder_count, file_count)
    """
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
                dt_info = get_media_file_datetime(file_path)
                base_name = _create_base_filename(dt_info, current_dir_name)
                new_filename = generate_unique_filename(
                    file_path.parent, base_name, extension
                )

                if filename != new_filename:
                    new_path = file_path.parent / new_filename
                    print(f"Would rename file: {file_path} -> {new_path}")
                    file_count += 1

    return folder_count, file_count


def main() -> int:
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
        root_path = Path(args.folder_path).resolve()

        if not root_path.exists():
            print(f"Error: Path does not exist: {root_path}")
            return 1

        if args.dry_run:
            print("Dry run - no actual changes will be made:")
            folder_count, file_count = _dry_run_folders(root_path)
            print(f"\nTotal folders that would be renamed: {folder_count}")
            print(f"Total files that would be renamed: {file_count}")
        else:
            result = rename_folders(str(root_path))
            print(f"\nTotal folders renamed: {len(result['folders'])}")
            print(f"Total files renamed: {len(result['files'])}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
