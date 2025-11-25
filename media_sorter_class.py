import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, List, Callable
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


class MediaSorter:
    def __init__(self, input_folder_path: Path, dry_mode: bool = True):
        self.input_folder_path = input_folder_path
        self.dry_mode = dry_mode
        self.n_files = 0
        self.n_folders = 0
        self.n_files_processed = 0
        self.n_folders = 0

    @classmethod
    def recursive_process(
        cls,
        folder_path: Path,
        directory_callable: Callable[[Path], bool] | None = None,
        files_callable: Callable[[Path], bool] | None = None,
    ):
        items = os.listdir(folder_path)
        directories = [item for item in items if (folder_path / item).is_dir()]
        files = [item for item in items if (folder_path / item).is_file()]
        for directory in directories:
            cls.recursive_process(
                folder_path / directory, directory_callable, files_callable
            )
            if directory_callable:
                directory_callable(folder_path / directory)

        if files_callable:
            for file in files:
                files_callable(folder_path / file)

    def walk_and_print_names(self):
        def print_item(file_path: Path):
            print(f"{"Directory" if file_path.is_dir() else "File"}: {file_path.name}")
            return True

        self.recursive_process(
            self.input_folder_path,
            directory_callable=print_item,
            files_callable=print_item,
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
        sorter.walk_and_print_names()

        # if args.dry_run:
        #     print("Dry run - no actual changes will be made:")
        #     # TODO: FIX COUNT
        #     dry_run_folders(root_path)
        # else:
        #     stats = rename_folders(str(root_path))
        #     # TODO: FIX COUNT
        #     print(f"\nTotal folders renamed: {len(stats.folders)}")
        #     print(f"Total files renamed: {len(stats.files)}")
        #
        # # Handle errors
        # if stats.errors:
        #     error_log_path = Path.cwd() / "error.log"
        #     _write_error_log(stats.errors, error_log_path)
        #     _display_error_summary(stats.errors)
        #     return 1  # Exit with error code if there were errors
        # else:
        #     # Clean up error log if it exists and there are no errors
        #     error_log_path = Path.cwd() / "error.log"
        #     if error_log_path.exists():
        #         error_log_path.unlink()

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
