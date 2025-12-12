import argparse
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ExifTags
from collections import namedtuple

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

# All supported datetime formats, from most specific to least specific
# Map format strings to output formats
EXIF_DT_FORMAT_MAP = {
    "%Y:%m:%d %H:%M:%S": "%Y%m%d%H%M%S",  # Standard EXIF: "2023:05:15 14:30:45"
    "%Y:%m:%d %H:%M": "%Y%m%d%H%M",  # Date with hour and minute: "2023:05:15 14:30"
    "%Y:%m:%d %H": "%Y%m%d%H",  # Date with hour: "2023:05:15 14"
    "%Y:%m:%d": "%Y%m%d",  # Date only: "2023:05:15"
    "%Y:%m": "%Y%m",  # Year and month: "2023:05"
    "%Y": "%Y",  # Year only: "2023"
}

# Named tuple to hold datetime and its format
DateTimeAndFormat = namedtuple("DateTimeAndFormat", ["datetime", "format_str"])


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
        formatted_title = self.format_folder_title(title) if title else ""

        # Build new folder name
        new_folder_name_array = []
        if date_str:
            new_folder_name_array.append(date_str)
        if formatted_title:
            new_folder_name_array.append(formatted_title)
        new_folder_name = "_".join(new_folder_name_array)

        self.show_progress()

        # Rename folder if needed
        if new_folder_name:
            new_folder_path = folder_path.parent / new_folder_name
            if new_folder_path != folder_path:
                if self.dry_mode:
                    pass
                    print(f" - Would rename folder: {folder_name} -> {new_folder_name}")
                else:
                    print(f" - Renaming folder: {folder_name} -> {new_folder_name}")
                    folder_path.rename(new_folder_path)
                return new_folder_path if not self.dry_mode else folder_path
        self.n_folders_processed += 1

        return folder_path

    def rename_file(self, file_path: Path) -> Path:
        """
        Rename a media file based on its metadata or parent directory name.

        Args:
            file_path: Path to the media file
        Returns:
            tuple: (old_path, new_path) if renamed, None if not renamed
        """
        parent_dir_name = file_path.parent.name
        extension = file_path.suffix.lower()

        if extension not in MEDIA_EXTENSIONS:
            return None

        # Try to extract datetime from metadata
        dt_info_exif = self.extract_datetimeinfo_from_exif(file_path)
        dt_info_filename = self.extract_datetimeinfo_from_filename(file_path.name)
        dt_info = (
            dt_info_exif
            or dt_info_filename
            or self.extract_datetimeinfo_from_folder_name(parent_dir_name)
        )

        should_write_exif = (
            dt_info_exif is None
            and dt_info_filename is not None
            and extension in MEDIA_EXTENSIONS
        )

        base_name = self.create_base_filename(dt_info, parent_dir_name)
        new_filename = self.generate_unique_filename(
            file_path.parent, base_name, extension
        )

        self.show_progress()

        # Rename file if needed
        if file_path.name != new_filename:
            if self.dry_mode:
                print(f" - Would rename file: {file_path.name} -> {new_filename}")
            else:
                print(f" - Renaming file: {file_path.name} -> {new_filename}")
                file_path.rename(file_path.parent / new_filename)
                # Optionally write EXIF DateTimeOriginal if missing
                if should_write_exif:
                    self.write_exif(file_path.parent / new_filename, dt_info)

        self.n_files_processed += 1

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
        pattern = r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?(?:\s(.+))?"
        match = re.match(pattern, folder_name)
        if not match:
            return "", folder_name

        # Build date string from available components
        year, month, day, title = match.groups()
        date_str = year + (month or "") + (day or "")

        # If no title provided after date, return "" for title
        return date_str, title or ""

    def format_folder_title(self, title: str) -> str:
        """
        Remove special characters, keeping alphanumeric (including Unicode), spaces.
        Preserve accented characters (é, à, ñ, ü, etc.)
        Replace spaces with hyphens and converting to lowercase.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with special characters removed
        """
        # Replace spaces and underscores with hyphens
        sanitized = re.sub(r"[\s]", "-", title)
        # We erase all non-word characters except hyphens and underscores
        sanitized = re.sub(r"[^\w\_\-]", "", sanitized, flags=re.UNICODE)
        # Clean up multi hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        return sanitized.lower()

    # Clean up multiple spaces and trim
    def create_base_filename(
        self, dt_info: DateTimeAndFormat, parent_dir_name: str
    ) -> str:
        """
        Create base filename from datetime and parent directory name.

        Args:
            dt_info: Tuple of (datetime, format_string) or None
            parent_dir_name: Name of the parent directory

        Returns:
            Base filename without extension

        Raises:
            ValueError: If both datetime and title are empty
        """
        dt, fmt = dt_info if dt_info else (None, None)
        folder_dt, folder_title = self.parse_folder_name(parent_dir_name)
        formatted_title = self.format_folder_title(folder_title) if folder_title else ""

        # If we have a datetime object from dt_info, use it
        if dt:
            if formatted_title:
                return f"{dt.strftime(fmt)}_{formatted_title}"
            else:
                return dt.strftime(fmt)

        # If we have a folder datetime string, try to extract datetime from it
        if folder_dt:
            folder_dt_info = self.extract_datetimeinfo_from_folder_name(parent_dir_name)
            if folder_dt_info:
                if formatted_title:
                    return f"{folder_dt_info.datetime.strftime(folder_dt_info.format_str)}_{formatted_title}"
                else:
                    return folder_dt_info.datetime.strftime(folder_dt_info.format_str)

        # Only title, no datetime
        if formatted_title:
            return formatted_title

        # Neither datetime nor title - this should not happen in normal operation
        raise ValueError("Cannot create filename: both datetime and title are empty")

    def generate_unique_filename(
        self, directory: Path, base_name: str, extension: str
    ) -> str:
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
        for counter in range(1, 1000):
            candidate = f"{base_name}_{counter:03d}{extension}"
            if not (directory / candidate).exists():
                return candidate

        raise ValueError(f"Too many files with base name {base_name}")

    def extract_datetimeinfo_from_exif(
        self, file_path: Path
    ) -> Optional[DateTimeAndFormat]:
        """
        Extract datetime from media file EXIF metadata.

        Args:
            file_path: Path to the media file

        Returns:
            Optional[MediaDateInfo]: datetime object if EXIF date found, None otherwise
        """

        try:
            with Image.open(file_path) as image:
                exif_data = image.getexif()
                if not exif_data:
                    return None
                for preferred_tag in DATETIME_EXIF_TAGS:
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id)
                        if tag == preferred_tag:
                            for (
                                format_str,
                                output_format,
                            ) in EXIF_DT_FORMAT_MAP.items():
                                try:
                                    dt = datetime.strptime(value, format_str)
                                    return DateTimeAndFormat(dt, output_format)
                                except (ValueError, TypeError):
                                    continue
        except Exception:
            pass
        return None

    def extract_datetimeinfo_from_filename(
        self, filename: str
    ) -> Optional[DateTimeAndFormat]:
        """
        Extract datetime from Signal or WhatsApp filename patterns.

        Supported patterns:
        - Signal: signal-YYYY-MM-DD-HH-MM-SS-randomtext.ext
        - WhatsApp: IMG-YYYYMMDD-WAxxx.ext or VID-YYYYMMDD-WAxxx.ext

        Args:
            filename: The filename to parse

        Returns:
            Optional[MediaDateInfo]: datetime object if pattern matches, None otherwise
        """
        # Wanted pattern: 20230515143045-randomtext.ext
        wanted_pattern = (
            r"^(\d{4})(?:(\d{2}))?(?:(\d{2}))?(?:(\d{2}))?(?:(\d{2}))?(?:(\d{2}))?"
        )
        match = re.match(wanted_pattern, filename)
        if match:
            try:
                year, month, day, hour, minute, second = match.groups()
                if second is not None:
                    format_str = "%Y%m%d%H%M%S"
                elif minute is not None:
                    format_str = "%Y%m%d%H%M"
                elif hour is not None:
                    format_str = "%Y%m%d%H"
                elif day is not None:
                    format_str = "%Y%m%d"
                elif month is not None:
                    format_str = "%Y%m"
                else:
                    format_str = "%Y"
                return DateTimeAndFormat(
                    datetime(
                        int(year),
                        int(month or 1),
                        int(day or 1),
                        int(hour or 0),
                        int(minute or 0),
                        int(second or 0),
                    ),
                    format_str,
                )
            except (ValueError, TypeError):
                pass

        # Signal pattern: signal-2023-05-15-14-30-45-randomtext.ext
        signal_pattern = r"signal-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})"
        match = re.match(signal_pattern, filename, re.IGNORECASE)
        if match:
            try:
                year, month, day, hour, minute, second = map(int, match.groups())
                return DateTimeAndFormat(
                    datetime(year, month, day, hour, minute, second),
                    "%Y%m%d%H%M%S",
                )
            except (ValueError, TypeError):
                pass

        # WhatsApp pattern: IMG-20230515-WA001.ext or VID-20230515-WA001.ext
        whatsapp_pattern = r"(?:IMG|VID)-(\d{4})(\d{2})(\d{2})-WA"
        match = re.match(whatsapp_pattern, filename, re.IGNORECASE)
        if match:
            try:
                year, month, day = map(int, match.groups())
                return DateTimeAndFormat(datetime(year, month, day), "%Y%m%d")
            except (ValueError, TypeError):
                pass

        # Other pattern: IMG-20230515-143045.ext or VID-20230515-143045.ext
        pattern = r"(?:IMG|VID)_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})"
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            try:
                year, month, day, hour, minute, second = map(int, match.groups())
                return DateTimeAndFormat(
                    datetime(year, month, day, hour, minute, second), "%Y%m%d%H%M%S"
                )
            except (ValueError, TypeError):
                pass

        return None

    def extract_datetimeinfo_from_folder_name(
        self,
        folder_name: str,
    ) -> Optional[DateTimeAndFormat]:
        """
        Extract datetime from folder name.

        Supports various date formats:
        - YYYYMMDD_title or YYYYMMDD-title -> datetime(YYYY, MM, DD)
        - YYYYMM_title or YYYYMM-title -> datetime(YYYY, MM, 1)
        - YYYY_title or YYYY-title -> datetime(YYYY, 1, 1)
        - YYYY-MM-DD Title -> datetime(YYYY, MM, DD)
        - YYYY-MM Title -> datetime(YYYY, MM, 1)
        - YYYY Title -> datetime(YYYY, 1, 1)

        Year ranges (YYYY-YYYY) are not supported and return None.

        Args:
            folder_name: The folder name to parse

        Returns:
            Optional[MediaDateInfo]: datetime object if date found, None otherwise
        """
        date_str, _ = self.parse_folder_name(folder_name)

        if not date_str:
            return None

        # Skip year ranges (e.g., "2020-2022")
        if "-" in date_str and len(date_str) == 9:  # Format: YYYY-YYYY
            return None

        # Remove any remaining hyphens from year ranges
        date_str = date_str.replace("-", "")

        # Parse based on length
        try:
            if len(date_str) == 8:  # YYYYMMDD
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                return DateTimeAndFormat(datetime(year, month, day), "%Y%m%d")
            elif len(date_str) == 6:  # YYYYMM
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                return DateTimeAndFormat(datetime(year, month, 1), "%Y%m")
            elif len(date_str) == 4:  # YYYY
                year = int(date_str)
                return DateTimeAndFormat(datetime(year, 1, 1), "%Y")
        except (ValueError, TypeError):
            pass

        return None

    def write_exif(self, file_path: Path, dt_info: DateTimeAndFormat):
        """
        Write EXIF DateTimeOriginal tag to the image file.

        Args:
            file_path: Path to the image file
            dt_info: DateTimeAndFormat object containing datetime and format string
        """
        try:
            with Image.open(file_path) as image:
                exif_data = image.getexif()
                if exif_data is None:
                    exif_data = {}

                for datetime_tag_name in DATETIME_EXIF_TAGS:
                    date_time_tag = None
                    for tag_id, tag_name in ExifTags.TAGS.items():
                        if tag_name == datetime_tag_name:
                            date_time_tag = tag_id
                            break

                    if date_time_tag is not None:
                        # Do not overwrite existing EXIF date
                        if bool(exif_data[date_time_tag]):
                            continue

                        exif_format = next(
                            (
                                exif_format
                                for exif_format, format_str in EXIF_DT_FORMAT_MAP.items()
                                if format_str == dt_info.format_str
                            ),
                            "%Y:%m:%d %H:%M:%S",
                        )
                        dt_str = dt_info.datetime.strftime(exif_format)
                        exif_data[date_time_tag] = dt_str
                        image.save(file_path, exif=exif_data)
        except Exception:
            pass

    def show_progress(self):
        """Display progress of processing."""
        if self.n_total_items > 0:
            percentage = (
                (self.n_files_processed + self.n_folders_processed)
                / self.n_total_items
                * 100
            )
            print(
                f"\nProcessing: {self.n_files_processed + self.n_folders_processed}/{self.n_total_items} ({percentage:.1f}%)",
                end="\033[F",
                # end="\r",
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
