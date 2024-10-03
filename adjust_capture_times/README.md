
# Image EXIF Time Adjuster

This script adjusts the capture times of image files based on camera serial numbers and provided time offsets. The adjustments are made using EXIF metadata, and the changes are logged in a database for future reference. This is especially useful when syncing images from multiple cameras that have different times.

## Features

- Extract EXIF data (including serial numbers and capture times) from images.
- Update the capture times (EXIF DateTimeOriginal) of images
- Log changes to a SQLite database for tracking.
- Support for different image formats (e.g., JPG, TIFF, NEF).
- Skips already processed files and supports ignoring folders.
- Handles RAW images using `exiftool` and standard formats using the Python Imaging Library (PIL).

## Requirements

- Python 3.x
- [Pillow (PIL)](https://python-pillow.org/) library
- [ExifTool](https://exiftool.org/) for handling RAW images (NEF)
- SQLite for storing processed file logs

### Python Libraries

Install the required libraries using `pip`:

```bash
pip install Pillow
```

### Install ExifTool

Follow the installation instructions for [ExifTool](https://exiftool.org/install.html).

## Setup

1. Download the python script.

2. Install dependencies.

3. Make sure ExifTool is installed and accessible from your terminal.

## Usage

1. Prepare a CSV or TXT file containing the time offsets for the camera serial numbers. Check the sample files for the correct format.

2. Run the script:

```bash
python adjust_capture_times.py
```

3. Follow the prompts to provide the folder to process and the offset file.

4. The script will process the images, adjusting the capture times, and will log the changes in `_file_updates.db` in the current directory.

### Log Files

Log files for each run are saved in the `_logs` folder with timestamps. These logs provide detailed information about each image file processed, any errors encountered, and the changes made.

### Database

The SQLite database (`_file_updates.db`) stores information about each file processed, including:

- File name
- File path
- Original capture time
- Updated capture time
- Processing timestamp
- Status (e.g., `changed`, `skipped`)

### Supported File Types

- JPG, JPEG
- TIFF
- NEF (via ExifTool)
