import sqlite3
from utils import fetch, titlextract, yearextract, resextract, codecextract

'''
DetailsExtractor class is used to extract details from the filenames of files in the filepaths table in the classified.db database.
It extracts the title, year, resolution, and codec of the files from their filenames and saves them to the details table in the classified.db database.
'''

class DetailsExtractor:
    '''Initialize DetailsExtractor class.'''
    def __init__(self):
        self.details = {} # Dictionary to store details extracted from filenames

    def extract(self):
        '''
        Extract details from filenames stored in the filepaths table.
        Constructs a dictionary of details extracted from filenames and saves it to the databases.
        '''
        # Fetch filenames and file_ids from the database
        filepaths = fetch(columns=['id', 'filename'], table_title='filepaths')

        # Extract details from filenames
        for filepath_tuple in filepaths: # Iterate over filepaths
            file_id = filepath_tuple[0] # Get file_id
            filename = filepath_tuple[1] # Get filename
            details = self.extract_details(filename) # Extract details from filename
            self.details[file_id] = details # Add details to dictionary

        # Save details to the database
        self.save_details()

    def extract_details(self, filename):
        '''
        Extract details from a filename.
        
        :param filename: The filename to extract details from
        :return: A dictionary of details extracted from the filename
        '''
        details = {} # Initialize details dictionary

        # Extract title
        details['title'] = titlextract(filename)

        # Extract year
        details['year'] = yearextract(filename)

        # Extract resolution
        details['resolution'] = resextract(filename)

        # Extract codec
        details['codec'] = codecextract(filename)

        return details
    
    def save_details(self):
        '''Save details to the database.'''
        # Connect to database
        conn = sqlite3.connect('../classified.db')
        c = conn.cursor()

        # Create details table if it does not exist
        c.execute('''CREATE TABLE IF NOT EXISTS filedetails
                     (file_id INTEGER PRIMARY KEY, title TEXT, year INTEGER, resolution TEXT, codec TEXT)''')

        # Insert or replace details into the details table
        for file_id, details in self.details.items():
            c.execute("INSERT OR REPLACE INTO filedetails VALUES (?, ?, ?, ?, ?)", (file_id, details['title'], details['year'], details['resolution'], details['codec']))

        # Commit changes and close connection
        conn.commit()
        conn.close()