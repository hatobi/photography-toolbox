import os
import csv
import logging
import time
import subprocess
from datetime import datetime, timedelta
from PIL import Image
from PIL.ExifTags import TAGS

# Generate a timestamped log filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f'adjust_capture_times_{timestamp}.log'

# Set up logging
logging.basicConfig(filename=log_filename, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# console.setFormatter(formatter)
# logging.getLogger().addHandler(console)

def get_exif(image_path):
    """Extract EXIF data from an image using exiftool for NEF files and PIL for others."""
    exif = {}

    # Handle NEF (RAW) files using exiftool
    if image_path.lower().endswith('.nef'):
        try:
            result = subprocess.run(['exiftool', '-json', image_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            exif_data = result.stdout.decode('utf-8')
            if exif_data:
                import json
                exif_json = json.loads(exif_data)[0]
                exif['DateTimeOriginal'] = exif_json.get('DateTimeOriginal')
                exif['SerialNumber'] = exif_json.get('SerialNumber')
                logging.info(f"Extracted serial number {exif['SerialNumber']} from {image_path}")
        except Exception as e:
            logging.error(f"Error extracting EXIF data from {image_path} using exiftool: {e}")

    else:
        # Handle other file types using Pillow
        try:
            img = Image.open(image_path)
            info = img._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    exif[decoded] = value
                exif['SerialNumber'] = str(info.get(42033, "")).strip()  # Correct tag and ensure serial number is treated as string
                logging.info(f"Extracted serial number {exif['SerialNumber']} from {image_path}")
        except Exception as e:
            logging.error(f"Error extracting EXIF data from {image_path}: {e}")
    
    return exif

def adjust_time(original_time, offset):
    """Adjust the capture time by the given offset."""
    return original_time + timedelta(seconds=offset)


def update_exif_time(image_path, new_time_str):
    """Update the EXIF DateTimeOriginal with the new time using exiftool."""
    try:
        subprocess.run(['exiftool', '-overwrite_original', f'-DateTimeOriginal={new_time_str}', image_path], check=True)
        logging.info(f"Updated EXIF DateTimeOriginal for {image_path} to {new_time_str}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update EXIF data for {image_path}: {e}")

def process_image(image_path, offset):
    """Process a single image file."""
    exif = get_exif(image_path)
    
    if 'DateTimeOriginal' in exif:
        original_time_str = exif['DateTimeOriginal']
        original_time = datetime.strptime(original_time_str, "%Y:%m:%d %H:%M:%S")
        new_time = adjust_time(original_time, offset)
        
        logging.info(f"Original time: {original_time_str} | New time: {new_time} for image: {image_path}")

        # Update EXIF data with the new time
        new_time_str = new_time.strftime("%Y:%m:%d %H:%M:%S")
        update_exif_time(image_path, new_time_str)
    else:
        logging.warning(f"No DateTimeOriginal found in {image_path}")

def process_folder(folder_path, offsets):
    """Process all images in a folder and subfolders, skipping files in '_ignore' directories."""
    total_files = sum([len(files) for _, _, files in os.walk(folder_path)])
    processed_files = 0
    start_time = time.time()

    for root, dirs, files in os.walk(folder_path):
        # Skip processing if the '_ignore' folder is in the path
        if '_ignore' in root.split(os.path.sep):
            logging.info(f"Skipping folder: {root} (in _ignore folder)")
            continue
        
        for file in files:
            if file.lower().endswith(('jpg', 'jpeg', 'tiff', 'nef')):
                image_path = os.path.join(root, file)
                exif = get_exif(image_path)
                
                serial_number = exif.get('SerialNumber', None)
                
                if serial_number is not None:
                    serial_number = str(serial_number).strip()  # Convert to string and strip spaces
                    if serial_number in offsets:
                        process_image(image_path, offsets[serial_number])
                        processed_files += 1
                    else:
                        logging.warning(f"No offset provided for serial number {serial_number} in {image_path}")
                else:
                    logging.warning(f"No serial number found in EXIF for {image_path}")

                # Calculate elapsed time and estimate remaining time
                elapsed_time = time.time() - start_time
                estimated_total_time = (elapsed_time / processed_files) * total_files if processed_files > 0 else 0
                remaining_time = estimated_total_time - elapsed_time
                remaining_time_str = str(timedelta(seconds=int(remaining_time))).split('.')[0]  # Format as HH:MM:SS

                # Print progress
                print(f"\r[{str(timedelta(seconds=int(elapsed_time)))}] {processed_files}/{total_files} files processed - Estimated time remaining: {remaining_time_str}", end='')

    print()  # New line after progress completion

def parse_offsets(offset_file):
    """Parse the CSV or text file for time offsets."""
    offsets = {}
    
    with open(offset_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            serial_number = row[0].strip()
            
            if len(row) == 2:
                offset = int(row[1].strip())
                offsets[serial_number] = offset
            elif len(row) == 3:
                image_path = row[1].strip()
                real_time_str = row[2].strip()
                
                try:
                    real_time = datetime.strptime(real_time_str, "%Y:%m:%d %H:%M:%S")
                except ValueError as e:
                    logging.error(f"Error parsing time for serial number {serial_number}: {e}")
                    continue
                
                exif = get_exif(image_path)
                if 'DateTimeOriginal' in exif:
                    original_time_str = exif['DateTimeOriginal']
                    try:
                        original_time = datetime.strptime(original_time_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError as e:
                        logging.error(f"Error parsing original time in EXIF for {image_path}: {e}")
                        continue
                    
                    offset = (real_time - original_time).total_seconds()
                    offsets[serial_number] = offset
                    logging.info(f"Calculated offset for serial number {serial_number}: {offset} seconds")
                else:
                    logging.warning(f"No DateTimeOriginal found in {image_path}")
    
    return offsets

def main():
    folder_to_process = input("Enter the folder path to process: ")
    offset_file = input("Enter the path to the offset CSV/TXT file: ")
    
    logging.info(f"Starting processing for folder: {folder_to_process} with offset file: {offset_file}")
    
    offsets = parse_offsets(offset_file)
    
    process_folder(folder_to_process, offsets)
    
    logging.info("Processing completed.")

if __name__ == "__main__":
    main()