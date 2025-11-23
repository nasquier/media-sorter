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


class TestShouldRename:
    """Tests for should_rename function."""

    def test_different_names(self):
        """Test that different names should be renamed."""
        assert should_rename("2023-01-15 My Photos", "20230115_my-photos") is True

    def test_same_names(self):
        """Test that same names should not be renamed."""
        assert should_rename("20230115_my-photos", "20230115_my-photos") is False


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
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 1
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
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 2
        assert (Path(self.test_dir) / "2023_vacation").exists()
        assert (Path(self.test_dir) / "2023_vacation" / "20230115_beach-day").exists()

    def test_no_rename_needed(self):
        """Test when folder is already in correct format."""
        # Create folder already in correct format
        test_folder = Path(self.test_dir) / "20230115_my-photos"
        test_folder.mkdir()

        # Rename folders
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 0
        assert test_folder.exists()

    def test_folder_without_date(self):
        """Test renaming folder without date."""
        # Create test folder without date
        test_folder = Path(self.test_dir) / "My Photos"
        test_folder.mkdir()

        # Rename folders
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 1
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
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 2
        assert (Path(self.test_dir) / "20230115_photos").exists()
        assert (Path(self.test_dir) / "20230220_videos").exists()

    def test_date_only_folder(self):
        """Test renaming folder with only a date."""
        # Create folder with only date
        test_folder = Path(self.test_dir) / "2023-01-15"
        test_folder.mkdir()

        # Rename folders
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 1
        assert (Path(self.test_dir) / "20230115").exists()
        assert not test_folder.exists()

    def test_year_month_format(self):
        """Test renaming folder with year-month format."""
        # Create folder with year-month
        test_folder = Path(self.test_dir) / "2023-01 January Photos"
        test_folder.mkdir()

        # Rename folders
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 1
        assert (Path(self.test_dir) / "202301_january-photos").exists()
        assert not test_folder.exists()

    def test_year_only_format(self):
        """Test renaming folder with year only format."""
        # Create folder with year only
        test_folder = Path(self.test_dir) / "2023 Annual Report"
        test_folder.mkdir()

        # Rename folders
        renamed = rename_folders(self.test_dir)

        # Check results
        assert len(renamed) == 1
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
