⚠️⚠️⚠️\
Mostly done with AI. 
I supervised the tasks and made sure the code works fine for my usage, but use it at your own risk.\
Please backup your files and check the code yourself before doing anything.\
I am not responsible of any problems or data loss following the execeution of this script.\
⚠️⚠️⚠️

# media-sorter
Rename and organize photos and videos with their metadata.\

## Description
A Python script that renames folders to follow a consistent naming convention based on dates and titles.

## Features
- Recursively processes folder trees from top to bottom
- Parses folder names with optional dates (YYYY-MM-DD, YYYY-MM, or YYYY)
- Renames folders to format: `{YYYYMMDD}_{title}` where:
  - Date is formatted without dashes
  - Title is lowercased
  - Spaces in title are replaced with dashes
- Renames media files (photos and videos) based on:
  - EXIF metadata timestamps (when available)
  - Parent folder name (as fallback)
  - Sanitizes filenames to remove problematic characters
- Dry-run mode to preview changes before applying
- Idempotent (won't rename already-formatted folders/files)

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt  
```

## Usage

Rename all folders in a directory:
```bash
python media_sorter.py /path/to/folder
```

Preview changes without actually renaming (dry-run):
```bash
python media_sorter.py --dry-run /path/to/folder
```

## Examples

### Input folders:
```
2023-01-15 My Photos/
2023-02 Vacation/
2024 Summer/
Random Folder/
```

### Output folders:
```
20230115_my-photos/
202302_vacation/
2024_summer/
random-folder/
```

## Development

### Running Tests
```bash
pytest test_media_sorter.py -v
```

### Code Formatting
```bash
black media_sorter.py test_media_sorter.py
```

### Code Linting
```bash
flake8 .
```

## Requirements
- Python 3.8+
- pytest >= 7.0.0
- black >= 23.0.0
- flake8 >= 6.0.0
- Pillow >= 10.0.0
