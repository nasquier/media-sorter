# Media Sorter

⚠️ **Disclaimer**: This project was developed with AI assistance. While thoroughly tested, please **backup your files** before use. The author is not responsible for any data loss or issues.

A Python script that intelligently organizes and renames photos and videos based on dates and EXIF metadata. The script processes directories recursively, renaming both folders and media files to a consistent, sortable format.

## Features Overview

### Folder Renaming
The script analyzes folder names and reformats them into a standardized pattern: `YYYYMMDD_title` or `YYYY-YYYY_title` for year ranges.

**Supported input formats:**
- Full dates: `2023-01-15 My Photos` → `20230115_my-photos`
- Year-month: `2023-01 Vacation` → `202301_vacation`  
- Year only: `2023 Summer` → `2023_summer`
- Year ranges: `2020-2022 Childhood` → `2020-2022_childhood`
- No date: `My Photos` → `my-photos`

**Smart text formatting:**
- Converts to lowercase with dashes replacing spaces
- Removes special characters (@, !, :, parentheses, etc.)
- **Preserves Unicode/accented characters** (é, à, ñ, ü, ç, etc.)
- Handles multiple spaces and trims whitespace

**Already-formatted folders** (like `20230515_vacation`) are detected and left unchanged, making the script **idempotent** - safe to run multiple times.

### Media File Renaming

The script renames media files using a sophisticated hierarchy of datetime sources:

#### 1. EXIF Metadata (Highest Priority)
For images, the script attempts to extract datetime from EXIF metadata tags in this order:
- `DateTimeOriginal` - When the photo was taken
- `DateTimeDigitized` - When the photo was digitized
- `DateTime` - General modification datetime

**Supported EXIF datetime formats** with precision preservation:
- `2023:05:15 14:30:45` → `20230515143045_title.jpg` (full datetime)
- `2023:05:15 14:30` → `202305151430_title.jpg` (no seconds)
- `2023:05:15 14` → `2023051514_title.jpg` (hour only)
- `2023:05:15` → `20230515_title.jpg` (date only)
- `2023:05` → `202305_title.jpg` (month only)
- `2023` → `2023_title.jpg` (year only)

#### 2. Filename Pattern Extraction (Medium Priority)
For files without EXIF (or non-images), the script recognizes common messaging app patterns:

**Signal pattern:**
- `signal-2023-05-15-14-30-45-abc123.jpg` → Extracts `2023-05-15 14:30:45`

**WhatsApp patterns:**
- `IMG-20230515-WA001.jpg` → Extracts `2023-05-15`
- `VID-20231225-WA999.mp4` → Extracts `2023-12-25`

**Generic camera patterns:**
- `IMG_20230515_143045.jpg` → Extracts `2023-05-15 14:30:45`

For Signal/WhatsApp files, the extracted datetime is **written to EXIF** (for images) to preserve it for future reads.

#### 3. Parent Folder Date (Lowest Priority)
When no EXIF or filename pattern is found, the script extracts the date from the parent folder name:
- File in `202305_vacation/` → Named `202305_vacation.jpg`
- File in `20230515_trip/` → Named `20230515_trip.jpg`

**Important:** Folder-based dates are NOT written to EXIF to preserve the original date precision (year, month, or full date).

#### Duplicate Handling
When multiple files would have the same name, automatic counters are added:
- First file: `20230515_vacation.jpg`
- Second file: `20230515_vacation_001.jpg`
- Third file: `20230515_vacation_002.jpg`

The counter system is smart enough to:
- Skip files already in the correct format (even with counters)
- Avoid renaming a file to remove its counter if it's already correct
- Not create unnecessary duplicates when re-running

#### Title Extraction
The title component comes from the parent folder name:
- Folder `20230515_vacation` → Title is `vacation`
- Folder `2023-05-15 My Trip` → Title is `my-trip` (formatted)

**Supported media formats:**
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

### Processing Behavior

**Bottom-to-Top Processing:**
The script processes directories from the deepest level upward (bottom-to-top) to ensure:
- Files are renamed before their parent folder
- Folder renames don't invalidate file paths
- Progress messages show final folder names, not intermediate states

**Progress Display:**
Real-time progress with percentage, showing:
- Total items processed
- Number of items renamed
- Number of items left untouched

Example: `3465/3465 (100.0%) processed, 904 renamed, 2561 untouched`

**Dry-Run Mode:**
Preview all changes without modifying anything:
```bash
python media_sorter.py --dry-run /path/to/folder
```

The dry-run accurately simulates:
- Which files/folders would be renamed
- What the new names would be
- Duplicate counter assignment
- Total count of changes

### Additional Features
- **Recursive processing** - Handles nested folder structures of any depth
- **Error resilience** - Continues processing even if individual files fail
- **Comprehensive error logging** - Failed operations logged to `error.log`
- **Exit codes** - Returns 1 if errors occurred, 0 on success
- **Test coverage** - 83 comprehensive tests covering all scenarios
- **CI/CD** - Automated testing via GitHub Actions

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

The project includes 83 comprehensive tests covering:

**Folder Operations:**
- All date format parsing (full date, year-month, year only, year ranges)
- Title extraction from formatted and unformatted folder names
- Special character sanitization with Unicode preservation
- Edge cases (empty titles, already-formatted names)

**EXIF Metadata:**
- All datetime precision levels (full to partial)
- Multiple EXIF tag priorities
- Invalid/corrupted EXIF handling
- Partial datetime formats (date+hour, date only, month only, year only)

**File Renaming:**
- Files with EXIF metadata
- Files without metadata (using folder dates)
- Signal/WhatsApp filename pattern extraction
- Generic camera filename patterns (`IMG_YYYYMMDD_HHMMSS`)
- Video files (no EXIF support)
- Duplicate handling with counters
- Already-correctly-named files (no unnecessary renames)

**EXIF Writing:**
- Writing EXIF for Signal/WhatsApp extracted dates
- NOT writing EXIF for folder-based dates (preserves precision)
- EXIF writing for images only (not videos)

**Integration Tests:**
- Combined folder and file renaming
- Nested folder structures
- Recursive processing
- Dry-run accuracy

**Total: 83 tests, 100% passing**

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
