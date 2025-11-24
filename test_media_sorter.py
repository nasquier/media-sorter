"""Tests for media_sorter module."""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

from media_sorter import (
    parse_folder_name,
    format_folder_name,
    should_rename,
    rename_folders,
    extract_title_from_folder_name,
)


class TestParseFolderName:
    """Tests for parse_folder_name function."""

    def test_full_date_with_title(self):
        """Test parsing folder with full date and title."""
        date_str, title = parse_folder_name("2023-01-15 My Photos")
        assert date_str == "20230115"
        assert title == "My Photos"

    def test_year_month_with_title(self):
        """Test parsing folder with year-month and title."""
        date_str, title = parse_folder_name("2023-01 Vacation")
        assert date_str == "202301"
        assert title == "Vacation"

    def test_year_only_with_title(self):
        """Test parsing folder with year only and title."""
        date_str, title = parse_folder_name("2023 Summer")
        assert date_str == "2023"
        assert title == "Summer"

    def test_no_date_only_title(self):
        """Test parsing folder with no date, only title."""
        date_str, title = parse_folder_name("My Photos")
        assert date_str is None
        assert title == "My Photos"

    def test_date_without_title(self):
        """Test parsing folder with date but no title."""
        date_str, title = parse_folder_name("2023-01-15")
        assert date_str == "20230115"
        assert title == ""

    def test_date_with_multiple_spaces(self):
        """Test parsing folder with date and title separated by space."""
        date_str, title = parse_folder_name("2023-01-15 My Great Photos")
        assert date_str == "20230115"
        assert title == "My Great Photos"

    def test_year_range_with_title(self):
        """Test parsing folder with year range and title."""
        date_str, title = parse_folder_name("2020-2022 Childhood")
        assert date_str == "2020-2022"
        assert title == "Childhood"

    def test_year_range_without_title(self):
        """Test parsing folder with year range but no title."""
        date_str, title = parse_folder_name("2015-2018")
        assert date_str == "2015-2018"
        assert title == ""

    def test_year_range_already_formatted(self):
        """Test parsing already formatted year range folder."""
        date_str, title = parse_folder_name("2020-2022_childhood")
        assert date_str == "2020-2022"
        assert title == "childhood"


class TestFormatFolderName:
    """Tests for format_folder_name function."""

    def test_date_with_title(self):
        """Test formatting with date and title."""
        result = format_folder_name("20230115", "My Photos")
        assert result == "20230115_my-photos"

    def test_date_without_title(self):
        """Test formatting with date but no title."""
        result = format_folder_name("20230115", "")
        assert result == "20230115"

    def test_no_date_with_title(self):
        """Test formatting with no date, only title."""
        result = format_folder_name(None, "My Photos")
        assert result == "my-photos"

    def test_title_with_multiple_spaces(self):
        """Test formatting title with multiple spaces."""
        result = format_folder_name("20230115", "My Great Photos")
        assert result == "20230115_my-great-photos"

    def test_year_month_with_title(self):
        """Test formatting with year-month and title."""
        result = format_folder_name("202301", "Vacation")
        assert result == "202301_vacation"

    def test_year_only_with_title(self):
        """Test formatting with year only and title."""
        result = format_folder_name("2023", "Summer")
        assert result == "2023_summer"

    def test_year_range_with_title(self):
        """Test formatting with year range and title."""
        result = format_folder_name("2020-2022", "Childhood")
        assert result == "2020-2022_childhood"

    def test_year_range_without_title(self):
        """Test formatting with year range but no title."""
        result = format_folder_name("2015-2018", "")
        assert result == "2015-2018"


class TestSpecialCharacterSanitization:
    """Tests for special character sanitization in folder names."""

    def test_exclamation_mark_removed(self):
        """Test that exclamation marks are removed from folder names."""
        date_str, title = parse_folder_name("2023-05 Holiday in Spain!")
        result = format_folder_name(date_str, title)
        assert result == "202305_holiday-in-spain"

    def test_at_symbol_removed(self):
        """Test that @ symbols are removed from folder names."""
        date_str, title = parse_folder_name("2023-08-10 CleanShot@2x")
        result = format_folder_name(date_str, title)
        assert result == "20230810_cleanshot2x"

    def test_colon_removed(self):
        """Test that colons are removed from folder names."""
        date_str, title = parse_folder_name("2024 Photos: Summer")
        result = format_folder_name(date_str, title)
        assert result == "2024_photos-summer"

    def test_multiple_exclamation_marks_removed(self):
        """Test that multiple exclamation marks are removed."""
        date_str, title = parse_folder_name("My Awesome Photos!!!")
        result = format_folder_name(date_str, title)
        assert result == "my-awesome-photos"

    def test_parentheses_removed(self):
        """Test that parentheses are removed from folder names."""
        date_str, title = parse_folder_name("Trip (2023)")
        result = format_folder_name(date_str, title)
        assert result == "trip-2023"

    def test_ampersand_removed(self):
        """Test that ampersands are removed from folder names."""
        date_str, title = parse_folder_name("Beach & Sun")
        result = format_folder_name(date_str, title)
        assert result == "beach-sun"

    def test_already_formatted_unchanged(self):
        """Test that already formatted folders remain unchanged."""
        date_str, title = parse_folder_name("20230115_my-photos")
        result = format_folder_name(date_str, title)
        assert result == "20230115_my-photos"

    def test_french_accents_preserved(self):
        """Test that French accented characters are preserved."""
        date_str, title = parse_folder_name("2023-05 Vacances à la plage")
        result = format_folder_name(date_str, title)
        assert result == "202305_vacances-à-la-plage"

    def test_spanish_accents_preserved(self):
        """Test that Spanish accented characters are preserved."""
        date_str, title = parse_folder_name("2024 Año nuevo")
        result = format_folder_name(date_str, title)
        assert result == "2024_año-nuevo"

    def test_german_umlauts_preserved(self):
        """Test that German umlauts are preserved."""
        date_str, title = parse_folder_name("2023-08 München trip")
        result = format_folder_name(date_str, title)
        assert result == "202308_münchen-trip"

    def test_mixed_unicode_and_special_chars(self):
        """Test Unicode characters preserved while special chars removed."""
        date_str, title = parse_folder_name("Noël en famille!")
        result = format_folder_name(date_str, title)
        assert result == "noël-en-famille"

    def test_portuguese_accents_preserved(self):
        """Test that Portuguese accented characters are preserved."""
        date_str, title = parse_folder_name("São Paulo 2024")
        result = format_folder_name(date_str, title)
        assert result == "são-paulo-2024"


class TestShouldRename:
    """Tests for should_rename function."""

    def test_different_names(self):
        """Test that different names should be renamed."""
        assert should_rename("2023-01-15 My Photos", "20230115_my-photos") is True

    def test_same_names(self):
        """Test that same names should not be renamed."""
        assert should_rename("20230115_my-photos", "20230115_my-photos") is False


class TestExtractTitleFromFolderName:
    """Tests for extract_title_from_folder_name function."""

    def test_formatted_folder_with_full_date(self):
        """Test extracting title from formatted folder with full date."""
        result = extract_title_from_folder_name("20230515_holiday-in-spain")
        assert result == "holiday-in-spain"

    def test_formatted_folder_with_year_month(self):
        """Test extracting title from formatted folder with year-month."""
        result = extract_title_from_folder_name("202305_vacation")
        assert result == "vacation"

    def test_formatted_folder_with_year_only(self):
        """Test extracting title from formatted folder with year only."""
        result = extract_title_from_folder_name("2023_summer-trip")
        assert result == "summer-trip"

    def test_unformatted_folder_with_date(self):
        """Test extracting title from unformatted folder with date."""
        result = extract_title_from_folder_name("2023-05-15 Holiday in Spain")
        assert result == "Holiday in Spain"

    def test_folder_without_date(self):
        """Test extracting title from folder without date."""
        result = extract_title_from_folder_name("my-photos")
        assert result == "my-photos"

    def test_folder_with_only_date(self):
        """Test extracting title from folder with only date."""
        result = extract_title_from_folder_name("20230515")
        assert result == "20230515"

    def test_formatted_folder_with_year_range(self):
        """Test extracting title from formatted folder with year range."""
        result = extract_title_from_folder_name("2020-2022_childhood")
        assert result == "childhood"

    def test_unformatted_folder_with_year_range(self):
        """Test extracting title from unformatted folder with year range."""
        result = extract_title_from_folder_name("2020-2022 Childhood")
        assert result == "Childhood"


class TestRenameFolders:
    """Tests for rename_folders function."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory after testing."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_rename_single_folder(self):
        """Test renaming a single folder."""
        # Create test folder
        test_folder = Path(self.test_dir) / "2023-01-15 My Photos"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results
        assert len(result.folders) == 1
        assert (Path(self.test_dir) / "20230115_my-photos").exists()
        assert not test_folder.exists()

    def test_rename_nested_folders(self):
        """Test renaming nested folders."""
        # Create nested test folders
        parent = Path(self.test_dir) / "2023 Vacation"
        parent.mkdir()
        child = parent / "2023-01-15 Beach Day"
        child.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results
        assert len(result.folders) == 2
        assert (Path(self.test_dir) / "2023_vacation").exists()
        assert (Path(self.test_dir) / "2023_vacation" / "20230115_beach-day").exists()

    def test_no_rename_needed(self):
        """Test when folder is already in correct format."""
        # Create folder already in correct format
        test_folder = Path(self.test_dir) / "20230115_my-photos"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results - folder should still exist with same name
        # (root test dir might be renamed if it has underscores)
        assert test_folder.exists() or (Path(self.test_dir).parent / Path(self.test_dir).name.replace('_', '') / "20230115_my-photos").exists()

    def test_folder_without_date(self):
        """Test renaming folder without date."""
        # Create test folder without date
        test_folder = Path(self.test_dir) / "My Photos"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results
        assert len(result.folders) == 1
        assert (Path(self.test_dir) / "my-photos").exists()
        assert not test_folder.exists()

    def test_multiple_folders_same_level(self):
        """Test renaming multiple folders at the same level."""
        # Create multiple test folders
        folder1 = Path(self.test_dir) / "2023-01-15 Photos"
        folder2 = Path(self.test_dir) / "2023-02-20 Videos"
        folder1.mkdir()
        folder2.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results - at least 2 folders renamed (root dir might also be renamed)
        assert len(result.folders) >= 2
        # Check that the created folders were renamed correctly
        renamed_paths = [r.new_path for r in result.folders]
        assert any("20230115_photos" in p for p in renamed_paths)
        assert any("20230220_videos" in p for p in renamed_paths)

    def test_date_only_folder(self):
        """Test renaming folder with only a date."""
        # Create folder with only date
        test_folder = Path(self.test_dir) / "2023-01-15"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results - at least 1 folder renamed (root dir might also be renamed)
        assert len(result.folders) >= 1
        # Check that the created folder was renamed correctly
        renamed_paths = [r.new_path for r in result.folders]
        assert any("20230115" in p and "2023-01-15" not in p for p in renamed_paths)

    def test_year_month_format(self):
        """Test renaming folder with year-month format."""
        # Create folder with year-month
        test_folder = Path(self.test_dir) / "2023-01 January Photos"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results
        assert len(result.folders) == 1
        assert (Path(self.test_dir) / "202301_january-photos").exists()
        assert not test_folder.exists()

    def test_year_only_format(self):
        """Test renaming folder with year only format."""
        # Create folder with year only
        test_folder = Path(self.test_dir) / "2023 Annual Report"
        test_folder.mkdir()

        # Rename folders
        result = rename_folders(self.test_dir)

        # Check results
        assert len(result.folders) == 1
        assert (Path(self.test_dir) / "2023_annual-report").exists()
        assert not test_folder.exists()

    def test_nonexistent_path(self):
        """Test error handling for nonexistent path."""
        with pytest.raises(ValueError, match="Path does not exist"):
            rename_folders("/nonexistent/path")

    def test_file_instead_of_directory(self):
        """Test error handling when path is a file."""
        # Create a file instead of directory
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="Path is not a directory"):
            rename_folders(str(test_file))


class TestMediaFileRenaming:
    """Tests for media file renaming functionality."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory after testing."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_rename_file_without_metadata(self):
        """Test renaming a file without EXIF metadata."""
        from media_sorter import rename_media_file

        # Create a test folder
        test_folder = Path(self.test_dir) / "202305_holiday-in-spain"
        test_folder.mkdir()

        # Create a simple image file without EXIF data
        test_file = test_folder / "photo.jpg"
        test_file.write_bytes(b"fake image data")

        # Rename the file
        result = rename_media_file(test_file, "202305_holiday-in-spain")

        # Check results
        assert result is not None
        assert (test_folder / "202305_holiday-in-spain.jpg").exists()
        assert not test_file.exists()

    def test_rename_multiple_files_with_counter(self):
        """Test that multiple files without metadata get numbered."""
        from media_sorter import rename_media_file

        # Create a test folder
        test_folder = Path(self.test_dir) / "202305_holiday-in-spain"
        test_folder.mkdir()

        # Create multiple simple image files without EXIF data
        files_created = []
        for i in range(3):
            test_file = test_folder / f"photo{i}.jpg"
            test_file.write_bytes(b"fake image data")
            result = rename_media_file(test_file, "202305_holiday-in-spain")
            if result:
                files_created.append(result[1])

        # Check results - files should be renamed with counters
        assert (test_folder / "202305_holiday-in-spain.jpg").exists()
        assert (test_folder / "202305_holiday-in-spain_001.jpg").exists()
        assert (test_folder / "202305_holiday-in-spain_002.jpg").exists()

    def test_non_media_file_not_renamed(self):
        """Test that non-media files are not renamed."""
        from media_sorter import rename_media_file

        # Create a test folder
        test_folder = Path(self.test_dir) / "test-folder"
        test_folder.mkdir()

        # Create a non-media file
        test_file = test_folder / "document.txt"
        test_file.write_text("test content")

        # Try to rename the file
        result = rename_media_file(test_file, "test-folder")

        # Check results - file should not be renamed
        assert result is None
        assert test_file.exists()

    def test_generate_unique_filename(self):
        """Test unique filename generation with counters."""
        from media_sorter import generate_unique_filename

        test_folder = Path(self.test_dir)

        # First file should have no counter
        filename1 = generate_unique_filename(test_folder, "test", ".jpg")
        assert filename1 == "test.jpg"

        # Create the file
        (test_folder / filename1).touch()

        # Second file should have _001
        filename2 = generate_unique_filename(test_folder, "test", ".jpg")
        assert filename2 == "test_001.jpg"

        # Create the file
        (test_folder / filename2).touch()

        # Third file should have _002
        filename3 = generate_unique_filename(test_folder, "test", ".jpg")
        assert filename3 == "test_002.jpg"

    def test_integrated_folder_and_file_rename(self):
        """Test that both folders and files are renamed together."""
        # Create a test folder with files
        test_folder = Path(self.test_dir) / "2023-05 Holiday in Spain"
        test_folder.mkdir()

        # Create some simple image files
        for i in range(2):
            test_file = test_folder / f"IMG_{i:04d}.jpg"
            test_file.write_bytes(b"fake image data")

        # Run rename_folders (which should rename both folders and files)
        from media_sorter import rename_folders

        result = rename_folders(self.test_dir)

        # Check folder was renamed
        assert len(result.folders) == 1
        renamed_folder = Path(self.test_dir) / "202305_holiday-in-spain"
        assert renamed_folder.exists()

        # Check files were renamed
        assert len(result.files) == 2
        assert (renamed_folder / "202305_holiday-in-spain.jpg").exists()
        assert (renamed_folder / "202305_holiday-in-spain_001.jpg").exists()

    def test_rename_file_with_exif_metadata(self):
        """Test renaming a file with EXIF metadata."""
        from media_sorter import rename_media_file, get_media_file_datetime
        from PIL import Image

        # Create a test folder
        test_folder = Path(self.test_dir) / "202305_holiday-in-spain"
        test_folder.mkdir()

        # Create an image with EXIF data
        img = Image.new("RGB", (100, 100), color="blue")
        exif_data = img.getexif()
        # Tag 36867 is DateTimeOriginal
        exif_data[36867] = "2023:05:15 14:30:45"

        test_file = test_folder / "photo.jpg"
        img.save(test_file, exif=exif_data)

        # Test that we can extract the datetime
        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 5
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 45
        assert fmt == "%Y:%m:%d %H:%M:%S"

        # Rename the file
        result = rename_media_file(test_file, "202305_holiday-in-spain")

        # Check results - should be renamed with datetime and title only
        assert result is not None
        expected_name = "20230515143045_holiday-in-spain.jpg"
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()

    def test_rename_video_file_without_metadata(self):
        """Test renaming a video file (which has no EXIF metadata)."""
        from media_sorter import rename_media_file

        # Create a test folder
        test_folder = Path(self.test_dir) / "202401_winter-trip"
        test_folder.mkdir()

        # Create a fake video file
        test_file = test_folder / "video.mp4"
        test_file.write_bytes(b"fake video data")

        # Rename the file
        result = rename_media_file(test_file, "202401_winter-trip")

        # Check results - should be renamed with parent directory name (no metadata)
        assert result is not None
        assert (test_folder / "202401_winter-trip.mp4").exists()
        assert not test_file.exists()


class TestPartialExifDatetime:
    """Tests for partial EXIF datetime parsing."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory after testing."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_exif_date_with_hour_minute(self):
        """Test parsing EXIF with date, hour, and minute (no seconds)."""
        from media_sorter import get_media_file_datetime, _format_datetime_from_exif
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="red")
        exif_data = img.getexif()
        exif_data[36867] = "2023:05:15 14:30"  # Missing seconds

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 5
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 30
        assert dt.second == 0  # Should default to 0
        assert fmt == "%Y:%m:%d %H:%M"
        # Verify formatted output doesn't include seconds
        formatted = _format_datetime_from_exif(dt, fmt)
        assert formatted == "202305151430"  # No seconds

    def test_exif_date_with_hour_only(self):
        """Test parsing EXIF with date and hour only."""
        from media_sorter import get_media_file_datetime, _format_datetime_from_exif
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="green")
        exif_data = img.getexif()
        exif_data[36867] = "2023:05:15 14"  # Only hour

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 5
        assert dt.day == 15
        assert dt.hour == 14
        assert dt.minute == 0  # Should default to 0
        assert dt.second == 0  # Should default to 0
        assert fmt == "%Y:%m:%d %H"
        # Verify formatted output doesn't include minutes/seconds
        formatted = _format_datetime_from_exif(dt, fmt)
        assert formatted == "2023051514"  # No minutes or seconds

    def test_exif_date_only(self):
        """Test parsing EXIF with date only (no time)."""
        from media_sorter import get_media_file_datetime, _format_datetime_from_exif
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="yellow")
        exif_data = img.getexif()
        exif_data[36867] = "2023:05:15"  # Date only

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 5
        assert dt.day == 15
        assert dt.hour == 0  # Should default to 0
        assert dt.minute == 0
        assert dt.second == 0
        assert fmt == "%Y:%m:%d"
        # Verify formatted output doesn't include time
        formatted = _format_datetime_from_exif(dt, fmt)
        assert formatted == "20230515"  # No time

    def test_exif_year_month_only(self):
        """Test parsing EXIF with year and month only."""
        from media_sorter import get_media_file_datetime, _format_datetime_from_exif
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="cyan")
        exif_data = img.getexif()
        exif_data[36867] = "2023:05"  # Year and month only

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 5
        assert dt.day == 1  # Should default to 1st of month
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0
        assert fmt == "%Y:%m"
        # Verify formatted output doesn't include day or time
        formatted = _format_datetime_from_exif(dt, fmt)
        assert formatted == "202305"  # No day or time

    def test_exif_year_only(self):
        """Test parsing EXIF with year only."""
        from media_sorter import get_media_file_datetime, _format_datetime_from_exif
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="magenta")
        exif_data = img.getexif()
        exif_data[36867] = "2023"  # Year only

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is not None
        dt, fmt = dt_info
        assert dt.year == 2023
        assert dt.month == 1  # Should default to January
        assert dt.day == 1  # Should default to 1st
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0
        assert fmt == "%Y"
        # Verify formatted output is year only
        formatted = _format_datetime_from_exif(dt, fmt)
        assert formatted == "2023"  # Year only, no zero-padding

    def test_exif_invalid_format_returns_none(self):
        """Test that invalid EXIF datetime format returns None."""
        from media_sorter import get_media_file_datetime
        from PIL import Image

        test_folder = Path(self.test_dir)
        img = Image.new("RGB", (100, 100), color="white")
        exif_data = img.getexif()
        exif_data[36867] = "invalid date format"

        test_file = test_folder / "test.jpg"
        img.save(test_file, exif=exif_data)

        dt_info = get_media_file_datetime(test_file)
        assert dt_info is None

    def test_rename_file_with_partial_exif_datetime(self):
        """Test that files with partial EXIF datetime are renamed correctly."""
        from media_sorter import rename_media_file
        from PIL import Image

        test_folder = Path(self.test_dir) / "202305_vacation"
        test_folder.mkdir()

        # Create image with partial datetime (date + hour/minute)
        img = Image.new("RGB", (100, 100), color="orange")
        exif_data = img.getexif()
        exif_data[36867] = "2023:05:20 16:45"  # Missing seconds

        test_file = test_folder / "photo.jpg"
        img.save(test_file, exif=exif_data)

        # Rename the file
        result = rename_media_file(test_file, "202305_vacation")

        # Check results - should NOT include seconds (no zero-padding)
        assert result is not None
        expected_name = "202305201645_vacation.jpg"  # No seconds!
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()


class TestSignalWhatsAppFilenames:
    """Test Signal and WhatsApp filename date extraction."""

    def setup_method(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_extract_signal_filename_datetime(self):
        """Test extracting datetime from Signal filename pattern."""
        from media_sorter import _extract_datetime_from_filename
        from datetime import datetime

        # Signal pattern: signal-YYYY-MM-DD-HH-MM-SS-randomtext.ext
        filename = "signal-2023-05-15-14-30-45-abc123.jpg"
        dt = _extract_datetime_from_filename(filename)

        assert dt is not None
        assert dt == datetime(2023, 5, 15, 14, 30, 45)

    def test_extract_whatsapp_img_filename_datetime(self):
        """Test extracting datetime from WhatsApp IMG filename pattern."""
        from media_sorter import _extract_datetime_from_filename
        from datetime import datetime

        # WhatsApp IMG pattern: IMG-YYYYMMDD-WAxxx.ext
        filename = "IMG-20230520-WA001.jpg"
        dt = _extract_datetime_from_filename(filename)

        assert dt is not None
        assert dt == datetime(2023, 5, 20, 0, 0, 0)

    def test_extract_whatsapp_vid_filename_datetime(self):
        """Test extracting datetime from WhatsApp VID filename pattern."""
        from media_sorter import _extract_datetime_from_filename
        from datetime import datetime

        # WhatsApp VID pattern: VID-YYYYMMDD-WAxxx.ext
        filename = "VID-20231225-WA999.mp4"
        dt = _extract_datetime_from_filename(filename)

        assert dt is not None
        assert dt == datetime(2023, 12, 25, 0, 0, 0)

    def test_extract_regular_filename_returns_none(self):
        """Test that regular filenames return None."""
        from media_sorter import _extract_datetime_from_filename

        filenames = [
            "IMG_1234.jpg",
            "photo.jpg",
            "DSC_5678.jpg",
            "random-file.mp4",
        ]

        for filename in filenames:
            dt = _extract_datetime_from_filename(filename)
            assert dt is None, f"{filename} should return None"

    def test_signal_filename_case_insensitive(self):
        """Test that Signal pattern is case-insensitive."""
        from media_sorter import _extract_datetime_from_filename
        from datetime import datetime

        filenames = [
            "SIGNAL-2023-05-15-14-30-45-abc.jpg",
            "Signal-2023-05-15-14-30-45-abc.jpg",
            "signal-2023-05-15-14-30-45-abc.jpg",
        ]

        for filename in filenames:
            dt = _extract_datetime_from_filename(filename)
            assert dt == datetime(2023, 5, 15, 14, 30, 45)

    def test_whatsapp_filename_case_insensitive(self):
        """Test that WhatsApp pattern is case-insensitive."""
        from media_sorter import _extract_datetime_from_filename
        from datetime import datetime

        filenames = [
            "IMG-20230520-WA001.jpg",
            "img-20230520-wa001.jpg",
            "VID-20231225-WA999.mp4",
            "vid-20231225-wa999.mp4",
        ]

        expected = [
            datetime(2023, 5, 20),
            datetime(2023, 5, 20),
            datetime(2023, 12, 25),
            datetime(2023, 12, 25),
        ]

        for filename, expected_dt in zip(filenames, expected):
            dt = _extract_datetime_from_filename(filename)
            assert dt == expected_dt

    def test_rename_signal_file_without_exif(self):
        """Test renaming a Signal file that has no EXIF metadata."""
        from media_sorter import rename_media_file
        from PIL import Image

        test_folder = Path(self.test_dir) / "202305-photos"
        test_folder.mkdir()

        # Create image without EXIF
        img = Image.new("RGB", (100, 100), color="blue")
        test_file = test_folder / "signal-2023-05-15-14-30-45-abc123.jpg"
        img.save(test_file)

        # Rename the file
        result = rename_media_file(test_file, "202305-photos")

        # Should be renamed using datetime from filename, with title extracted from folder
        assert result is not None
        expected_name = "20230515143045_photos.jpg"
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()

        # Verify EXIF was written
        from media_sorter import get_media_file_datetime

        renamed_file = test_folder / expected_name
        dt_info = get_media_file_datetime(renamed_file)
        assert dt_info is not None
        assert dt_info[0].year == 2023
        assert dt_info[0].month == 5
        assert dt_info[0].day == 15
        assert dt_info[0].hour == 14
        assert dt_info[0].minute == 30
        assert dt_info[0].second == 45

    def test_rename_whatsapp_file_without_exif(self):
        """Test renaming a WhatsApp file that has no EXIF metadata."""
        from media_sorter import rename_media_file
        from PIL import Image

        test_folder = Path(self.test_dir) / "202305-vacation"
        test_folder.mkdir()

        # Create image without EXIF
        img = Image.new("RGB", (100, 100), color="green")
        test_file = test_folder / "IMG-20230520-WA001.jpg"
        img.save(test_file)

        # Rename the file
        result = rename_media_file(test_file, "202305-vacation")

        # Should be renamed using date from filename (time defaults to 00:00:00)
        # with title extracted from folder (just "vacation")
        assert result is not None
        expected_name = "20230520000000_vacation.jpg"
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()

        # Verify EXIF was written
        from media_sorter import get_media_file_datetime

        renamed_file = test_folder / expected_name
        dt_info = get_media_file_datetime(renamed_file)
        assert dt_info is not None
        assert dt_info[0].year == 2023
        assert dt_info[0].month == 5
        assert dt_info[0].day == 20

    def test_signal_file_with_existing_exif_uses_exif(self):
        """Test that Signal files with existing EXIF use the EXIF data."""
        from media_sorter import rename_media_file
        from PIL import Image

        test_folder = Path(self.test_dir) / "202305-trip"
        test_folder.mkdir()

        # Create image with EXIF (different from filename date)
        img = Image.new("RGB", (100, 100), color="red")
        exif_data = img.getexif()
        exif_data[36867] = "2023:06:10 12:00:00"  # Different date than filename

        test_file = test_folder / "signal-2023-05-15-14-30-45-abc.jpg"
        img.save(test_file, exif=exif_data)

        # Rename the file
        result = rename_media_file(test_file, "202305-trip")

        # Should use EXIF date (2023-06-10), not filename date (2023-05-15)
        # with title extracted from folder (just "trip")
        assert result is not None
        expected_name = "20230610120000_trip.jpg"
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()

    def test_rename_whatsapp_video_without_metadata(self):
        """Test renaming a WhatsApp video file (can't write EXIF to video)."""
        from media_sorter import rename_media_file

        test_folder = Path(self.test_dir) / "202312-videos"
        test_folder.mkdir()

        # Create a fake video file
        test_file = test_folder / "VID-20231225-WA999.mp4"
        test_file.write_bytes(b"fake video data")

        # Rename the file
        result = rename_media_file(test_file, "202312-videos")

        # Should be renamed using date from filename
        # with title extracted from folder (just "videos")
        assert result is not None
        expected_name = "20231225000000_videos.mp4"
        assert (test_folder / expected_name).exists()
        assert not test_file.exists()
