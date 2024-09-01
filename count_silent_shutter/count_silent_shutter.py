import os
import sqlite3
import subprocess
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Database setup
db_name = "exif_data.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

def create_table_with_columns(exif_data):
    # Create table if it doesn't exist with dynamic columns
    columns = ["file_path TEXT UNIQUE"]
    for key in exif_data.keys():
        column_name = key.replace(" ", "_").replace("-", "_")  # Replace spaces and hyphens to avoid SQL syntax issues
        columns.append(f'"{column_name}" TEXT')  # Store all EXIF data as TEXT
    
    columns_str = ", ".join(columns)
    cursor.execute(f'CREATE TABLE IF NOT EXISTS exif_data ({columns_str})')
    conn.commit()
    logging.debug("Created database table with columns: %s", columns_str)

def add_columns_if_not_exist(exif_data):
    # Add any missing columns dynamically
    existing_columns = [col[1] for col in cursor.execute("PRAGMA table_info(exif_data)").fetchall()]
    for key in exif_data.keys():
        column_name = key.replace(" ", "_").replace("-", "_")
        if column_name not in existing_columns:
            cursor.execute(f'ALTER TABLE exif_data ADD COLUMN "{column_name}" TEXT')
            conn.commit()
            logging.debug("Added new column to database: %s", column_name)

def insert_exif_data(file_path, exif_data):
    # Prepare data for insertion
    columns = ["file_path"]
    values = [file_path]
    
    for key, value in exif_data.items():
        column_name = key.replace(" ", "_").replace("-", "_")
        columns.append(f'"{column_name}"')
        values.append(str(value))  # Convert value to string for uniformity

    columns_str = ", ".join(columns)
    placeholders = ", ".join("?" for _ in values)
    
    cursor.execute(f'INSERT OR IGNORE INTO exif_data ({columns_str}) VALUES ({placeholders})', values)
    conn.commit()
    logging.debug("Inserted EXIF data into database for file: %s", file_path)

def get_exif_data(file_path):
    # Use exiftool to get the exif data
    result = subprocess.run(["exiftool", "-j", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        logging.error("Error reading EXIF data from %s: %s", file_path, result.stderr.decode())
        return None
    exif_data = json.loads(result.stdout.decode())
    logging.debug("Extracted EXIF data from file: %s", file_path)
    return exif_data[0] if exif_data else None

def process_photo(file_path, serial_number_to_check):
    logging.info("Processing photo: %s", file_path)
    exif_data = get_exif_data(file_path)
    if exif_data is None:
        logging.warning("No EXIF data found for file: %s", file_path)
        return
    
    serial_number = exif_data.get('SerialNumber')
    
    # Ensure both are strings before comparison
    if str(serial_number) == str(serial_number_to_check):
        logging.info("Serial number matches: %s", serial_number)
        add_columns_if_not_exist(exif_data)  # Ensure all columns exist
        insert_exif_data(file_path, exif_data)  # Insert EXIF data into the database
    else:
        logging.info("Serial number does not match for file: %s (found: %s, expected: %s)", file_path, serial_number, serial_number_to_check)


def scan_folder(folder_path, serial_number_to_check):
    logging.info("Scanning folder: %s", folder_path)
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.dng', '.nef', '.cr2')):
                file_path = os.path.join(root, file)
                cursor.execute('SELECT COUNT(*) FROM exif_data WHERE file_path = ?', (file_path,))
                if cursor.fetchone()[0] == 0:  # If the file is not already in the database
                    process_photo(file_path, serial_number_to_check)
                else:
                    logging.debug("File already in database, skipping: %s", file_path)

def analyze_data():
    cursor.execute('SELECT COUNT(*) FROM exif_data WHERE SilentPhotography = "On"')
    silent_on = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM exif_data WHERE SilentPhotography = "Off"')
    silent_off = cursor.fetchone()[0]
    
    return silent_on, silent_off

if __name__ == "__main__":
    input_folder = input("Enter the path to the folder containing your photos: ")
    serial_number_to_check = input("Enter the serial number of the camera: ")

    # Step 1: Scan folder and process photos
    first_file = True
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.dng', '.nef', '.cr2')):
                file_path = os.path.join(root, file)
                exif_data = get_exif_data(file_path)
                if exif_data and first_file:
                    create_table_with_columns(exif_data)
                    first_file = False
                process_photo(file_path, serial_number_to_check)

    # Step 2: Analyze the data
    silent_on_count, silent_off_count = analyze_data()

    print(f"Photos with silent photography ON: {silent_on_count}")
    print(f"Photos with silent photography OFF: {silent_off_count}")

# Clean up
conn.close()
