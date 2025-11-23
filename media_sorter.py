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


def rename_folders(root_path):
    """
    Recursively rename folders in the directory tree from top to bottom.

    Args:
        root_path: Root directory path to start processing

    Returns:
        list: List of tuples (old_path, new_path) for renamed folders
    """
    root_path = Path(root_path).resolve()

    if not root_path.exists():
        raise ValueError(f"Path does not exist: {root_path}")

    if not root_path.is_dir():
        raise ValueError(f"Path is not a directory: {root_path}")

    renamed_folders = []

    # Walk the directory tree from top to bottom
    # We need to process in sorted order to ensure consistent behavior
    for dirpath, dirnames, _ in os.walk(root_path, topdown=True):
        # Sort dirnames to process in consistent order
        dirnames.sort()

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

        # Perform renames (we do this after collecting to avoid issues with iteration)
        for old_path, new_path, old_name, new_name in dirs_to_rename:
            try:
                old_path.rename(new_path)
                renamed_folders.append((str(old_path), str(new_path)))
                print(f"Renamed: {old_path} -> {new_path}")

                # Update dirnames list to reflect the rename
                idx = dirnames.index(old_name)
                dirnames[idx] = new_name
            except Exception as e:
                print(f"Error renaming {old_path} to {new_path}: {e}")

    return renamed_folders


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Rename folders with date and title formatting."
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
            for dirpath, dirnames, _ in os.walk(root_path, topdown=True):
                dirnames.sort()
                for dirname in dirnames:
                    date_str, title = parse_folder_name(dirname)
                    new_name = format_folder_name(date_str, title)
                    if should_rename(dirname, new_name):
                        old_path = Path(dirpath) / dirname
                        new_path = Path(dirpath) / new_name
                        print(f"Would rename: {old_path} -> {new_path}")
        else:
            renamed = rename_folders(args.folder_path)
            print(f"\nTotal folders renamed: {len(renamed)}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
