import argparse
import os
import re
from pathlib import Path
from typing import Optional, Tuple

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


class MediaSorter:
    def __init__(self, input_folder_path: Path, dry_mode: bool = False):
        self.input_folder_path = input_folder_path
        self.dry_mode = dry_mode
        self.n_files = 0
        self.n_folders = 0
        self.n_files_processed = 0
        self.n_folders_processed = 0
        self.n_total_items = 0

        for _, dirnames, filenames in os.walk(input_folder_path, topdown=True):
            self.n_folders += len(dirnames)
            self.n_files += sum(
                1 for f in filenames if Path(f).suffix.lower() in MEDIA_EXTENSIONS
            )

        self.n_total_items = self.n_files + self.n_folders

    def recursive_renaming(
        self,
        folder_path: Path,
    ):
        # Rename folder
        new_folder_path = self.rename_folder(folder_path)

        # List folder items
        items = os.listdir(new_folder_path)
        folders = [item for item in items if (new_folder_path / item).is_dir()]
        files = [item for item in items if (new_folder_path / item).is_file()]

        # Recursive operation in child folders
        for folder in folders:
            self.recursive_renaming(new_folder_path / folder)

        # Rename files in folder
        for file in files:
            self.rename_file(new_folder_path / file)

    def rename_folder(self, folder_path: Path) -> Path:
        """Rename folder based on date and title extracted from its name."""
        # Parse folder name
        folder_name = folder_path.name
        date_str, title = self.parse_folder_name(folder_name)
        formatted_title = title.replace(" ", "-").lower()

        # Build new folder name
        new_folder_name_array = []
        if date_str:
            new_folder_name_array.append(date_str)
        if formatted_title:
            new_folder_name_array.append(formatted_title)
        new_folder_name = "_".join(new_folder_name_array)

        # Print progress
        self.n_folders_processed += 1
        self.show_progress()
        print(
            f" - {'Renaming' if not self.dry_mode else 'Would rename'} folder: {folder_name} -> {new_folder_name}"
        )

        # Rename folder if needed
        if new_folder_name:
            new_folder_path = folder_path.parent / new_folder_name
            if new_folder_path != folder_path:
                if not self.dry_mode:
                    folder_path.rename(new_folder_path)
                    return new_folder_path
        return folder_path

    def rename_file(self, file_path: Path):
        return file_path

    def parse_folder_name(
        self, folder_name: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse folder name to extract date and title.

        Date format: YYYY-MM-DD (month and day are optional) or YYYY-YYYY (year range)
        Examples:
            - "2023-01-15 My Photos" -> date: "20230115", title: "My Photos"
            - "2023-01 Vacation" -> date: "202301", title: "Vacation"
            - "2023 Summer" -> date: "2023", title: "Summer"
            - "2020-2022 Childhood" -> date: "2020-2022", title: "Childhood"
            - "2023" -> date: "2023", title: ""
            - "My Photos" -> date: "", title: "My Photos"
            - "20230115_my-photos" -> date: "20230115", title: "my-photos"
            (already formatted)

        Args:
            folder_name: The original folder name

        Returns:
            tuple: (date_str, title) where date_str is formatted without dashes
                and title is the remaining part
        """
        # First check if it's already in formatted form:
        # YYYYMMDD_title or YYYYMM_title or YYYY_title or YYYY-YYYY_title
        pattern = r"^(\d{4}(?:-\d{4}|\d{4}|\d{2})?)(?:_(.+))?$"
        match = re.match(pattern, folder_name)
        if match:
            date_str, title = match.groups()
            return date_str, title

        # Check for year range: YYYY-YYYY optionally followed by space and title
        pattern = r"(\d{4}-\d{4})(?:\s+(.*))?"
        match = re.match(pattern, folder_name)
        if match:
            date_str, title = match.groups()
            return date_str, title

        # Pattern to match optional date at the start
        # YYYY-MM-DD or YYYY-MM or YYYY optionally followed by space and title
        pattern = r"^(\d{4})(?:-(\d{2}))(?:-(\d{2}))(?:\s(.+))?$"
        match = re.match(pattern, folder_name)
        if not match:
            return "", folder_name

        # Build date string from available components
        year, month, day, title = match.groups()
        date_str = year + (month or "") + (day or "")

        # If no title provided after date, return "" for title
        return date_str, title or ""

    def show_progress(self):
        """Display progress of processing."""
        if self.n_total_items > 0:
            percentage = (
                (self.n_files_processed + self.n_folders_processed)
                / self.n_total_items
                * 100
            )
            print(
                f"\rProcessing: {self.n_files_processed + self.n_folders_processed}/{self.n_total_items} ({percentage:.1f}%)",
                end="",
                flush=True,
            )


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

        sorter = MediaSorter(root_path, dry_mode=args.dry_run)
        sorter.recursive_renaming(root_path)

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
