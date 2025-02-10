import os
import re
import sqlite3

class Scanner:
    '''
    Scanner class to scan a directory for files with specific extensions

    Args:
    directory (str): The directory to scan
    extensions (list): List of extensions to search for. If empty, search for all files

    Attributes:
    directory (str): The directory to scan
    extensions (list): List of extensions to search for. If empty, search for all files
    files (list): List of files

    Methods:
    pathfinder: Scans the directory for files with specific extensions and saves the file paths to the database
    pathextractor: Extracts metadata such type, genre, franchise/show/film etc. from the path of the files
    nameextractor: Extracts the name, resolution, and year of release of the files from its name

    '''
    def __init__(self, directory, extensions): # Constructor
        self.directory = directory # Directory to scan
        self.extensions = extensions # Extensions to search for
        self.files = [] # List of files
        self.conn = sqlite3.connect('classified.db') # Connect to SQLite database
        self.create_table() # Create table if it doesn't exist

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS filepaths (
                    id INTEGER PRIMARY KEY,
                    filepath TEXT UNIQUE
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS filesteps (
                    id INTEGER PRIMARY KEY,
                    filepath_id INTEGER,
                    step TEXT,
                    FOREIGN KEY (filepath_id) REFERENCES filepaths(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS filedetails (
                    id INTEGER PRIMARY KEY,
                    filepath_id INTEGER,
                    name TEXT,
                    resolution TEXT,
                    year INTEGER,
                    FOREIGN KEY (filepath_id) REFERENCES filepaths(id)        
                )
            ''')

    def pathfinder(self): # Scans the directory for files with specific extensions
        for root, _, files in os.walk(self.directory): # Loop through the files in the directory
            for file in files:
                if file.endswith(tuple(self.extensions)): # Check if the file has the specified extension
                    filepath = os.path.join(root, file) # Get the full file path
                    self.save_filepath(filepath) # Save the file path to the database
                    self.files.append(filepath) # Append the file path to the list of files
            for directory in os.listdir(root):
                if os.path.isdir(os.path.join(root, directory)):
                    self.directory = os.path.join(root, directory)
                    self.pathfinder() # Recursively call the pathfinder function

    def save_filepath(self, filepath): # Save the file path to the database
        with self.conn:
            self.conn.execute('''
                INSERT OR IGNORE INTO filepaths (filepath) VALUES (?)
            ''', (filepath,))
            self.conn.commit() # Commit the changes to the database

    def pathextractor(self): # Extract metadata such as type, genre, franchise/show/film etc. from the path of the files
        for filepath in self.files:
            cursor = self.conn.execute('SELECT id FROM filepaths WHERE filepath = ?', (filepath,))
            filepath_id = cursor.fetchone()[0] # Get the id of the file path
            steps = filepath.split(os.sep) # Split the file path into steps
            for step in steps:
                if not step.endswith(tuple(self.extensions)): # Ignore the media file itself
                    self.save_step(filepath_id, step) # Save the step to the database

    def save_step(self, filepath_id, step): # Save the step to the database
        with self.conn:
            self.conn.execute('''
                INSERT INTO filesteps (filepath_id, step) VALUES (?, ?)
            ''', (filepath_id, step))
            self.conn.commit() # Commit the changes to the database

    def nameextractor(self): # Extract the name, resolution, and year of release of the files from its name
        for filepath in self.files:
            filename = os.path.basename(filepath) # Get the file name from the file path e.g. 'The.Matrix.1999.1080p.mkv'
            name, resolution, year = self.extact_details(filename) # Extract the name, resolution, and year from the file name
            cursor = self.conn.execute('SELECT id FROM filepaths WHERE filepath = ?', (filepath,))
            filepath_id = cursor.fetchone()[0] # Get the id of the file path
            self.save_details(filepath_id, name, resolution, year) # Save the details to the database

    def extract_details(self, filename): # Extract the name, resolution, and year from the file name
        name = re.sub(r'\.\w+$', '', filename) # Remove the extension from the file name
        resolution = re.search(r'\d{3,4}p', filename)
        resolution = resolution.group() if resolution else None # Extract the resolution from the file name
        year = re.search(r'\b(19|20)\d{2}\b', filename) # Extract the year from the file name
        year = int(year.group()) if year else None
        return name, resolution, year
    
    def save_details(self, filepath_id, name, resolution, year): # Save the details to the database
        with self.conn:
            self.conn.execute('''
                INSERT INTO filedetails (filepath_id, name, resolution, year) VALUES (?, ?, ?, ?)
            ''', (filepath_id, name, resolution, year))
            self.conn.commit() # Commit the changes to the database