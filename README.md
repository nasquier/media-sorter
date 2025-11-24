# Media Sorter

⚠️ **Disclaimer**: This project was developed with AI assistance. While thoroughly tested, please **backup your files** before use. The author is not responsible for any data loss or issues.

A Python script that intelligently organizes and renames photos and videos based on dates and EXIF metadata.

## Features

### Folder Renaming
- **Date formats supported:**
  - Full dates: `2023-01-15 My Photos` → `20230115_my-photos`
  - Year-month: `2023-01 Vacation` → `202301_vacation`
  - Year only: `2023 Summer` → `2023_summer`
  - **Year ranges**: `2020-2022 Childhood` → `2020-2022_childhood`
- **Smart formatting:**
  - Converts to lowercase
  - Replaces spaces with dashes
  - Removes special characters (@, !, :, etc.)
  - **Preserves Unicode/accented characters** (é, à, ñ, ü, etc.)
- **Idempotent**: Already-formatted folders remain unchanged

### Media File Renaming
- **EXIF metadata support:**
  - Extracts datetime from image EXIF data
  - Supports partial dates (year only, year+month, etc.)
  - No zero-padding for partial dates
- **Fallback naming**: Uses parent folder name when EXIF unavailable
- **Smart filename generation:**
  - Format: `{datetime}_{folder-title}.{ext}`
  - Automatic duplicate handling (adds `_001`, `_002`, etc.)
- **Supported formats:**
  - Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`
  - Videos: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

### Additional Features
- Recursive processing (top-down)
- Dry-run mode to preview changes
- Comprehensive test coverage (63 tests)
- CI/CD with GitHub Actions

## Installation

```bash
# Clone the repository
git clone https://github.com/nasquier/media-sorter.git
cd media-sorter

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Rename folders and files in a directory
python media_sorter.py /path/to/folder

# Preview changes without modifying files (dry-run)
python media_sorter.py --dry-run /path/to/folder
```

### Examples

**Input structure:**
```
/photos/
  ├── 2023-01-15 My Photos!/
  │   ├── IMG_1234.jpg (EXIF: 2023-01-15 14:30:45)
  │   └── video.mp4
  ├── 2023-05 Vacances à la plage/
  │   └── photo@beach.jpg
  ├── 2020-2022 Childhood !/
  └── Random Folder/
```

**Output structure:**
```
/photos/
  ├── 20230115_my-photos/
  │   ├── 20230115143045_my-photos.jpg
  │   └── 20230115_my-photos.mp4
  ├── 202305_vacances-à-la-plage/
  │   └── 202305_vacances-à-la-plage.jpg
  ├── 2020-2022_childhood/
  └── random-folder/
```

## Error Handling

When errors occur during processing (e.g., permission denied, file in use), the script:

1. **Continues processing** - Errors don't stop the entire operation
2. **Logs to `error.log`** - All failed operations are written to this file in the current directory
3. **Displays a summary** - At the end, shows all errors encountered
4. **Returns exit code 1** - If any errors occurred (useful for CI/CD)

**Example error.log:**
```
Error processing files/folders - 2 errors encountered:

1. Path: /photos/locked/IMG_1234.jpg
   Type: PermissionError
   Message: [Errno 13] Permission denied: '/photos/locked/IMG_1234.jpg'

2. Path: /photos/corrupt/photo.jpg
   Type: PIL.UnidentifiedImageError
   Message: cannot identify image file
```

The `error.log` file is automatically:
- Created only when errors occur
- Removed if no errors are found
- Ignored by git (listed in `.gitignore`)

## Development

### Running Tests

```bash
# Run all tests
pytest test_media_sorter.py -v

# Run specific test class
pytest test_media_sorter.py::TestSpecialCharacterSanitization -v

# Run with coverage
pytest test_media_sorter.py --cov=media_sorter
```

### Code Quality

```bash
# Format code
black media_sorter.py test_media_sorter.py

# Lint code
flake8 .

# Run all checks
black --check . && flake8 . && pytest test_media_sorter.py
```

### CI/CD

GitHub Actions workflow runs automatically on push/PR:
- Code formatting check (Black)
- Linting (flake8)
- Tests (pytest) on Python 3.8, 3.9, 3.10, 3.11

## Requirements

- Python 3.8+
- Pillow >= 10.0.0 (EXIF metadata extraction)
- pytest >= 7.0.0 (testing)
- black >= 23.0.0 (formatting)
- flake8 >= 6.0.0 (linting)

## Test Coverage

The project includes comprehensive tests covering:
- **Folder parsing**: All date formats including year ranges
- **Title formatting**: Special character removal, Unicode preservation
- **EXIF extraction**: All datetime formats (full to partial)
- **File renaming**: With/without metadata, duplicate handling
- **Edge cases**: Empty titles, already-formatted names, etc.

**Total: 63 tests, 100% passing**

## Supported Date Formats

### Input Formats
- `YYYY-MM-DD Title` → Full date
- `YYYY-MM Title` → Year and month
- `YYYY Title` → Year only
- `YYYY-YYYY Title` → Year range (e.g., 2020-2022)

### EXIF Datetime Formats
- `%Y:%m:%d %H:%M:%S` → Full datetime
- `%Y:%m:%d %H:%M` → Date + hour/minute
- `%Y:%m:%d %H` → Date + hour
- `%Y:%m:%d` → Date only
- `%Y:%m` → Year + month
- `%Y` → Year only

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass: `pytest test_media_sorter.py`
2. Code is formatted: `black .`
3. No linting errors: `flake8 .`

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Developed with AI assistance (GitHub Copilot / Claude)
- EXIF handling powered by Pillow
- Testing with pytest
