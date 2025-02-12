from utils import pathextract, fetch
import os
import sqlite3

'''
StepExtractor class is a PathFinder class used to extract directory steps from a filepath.
It takes file paths from the saved filepaths table in the classified.db database and 
extracts the directory steps from the file paths by removing the root directory and filename.
'''

class StepExtractor:
    # Initialize StepExtractor class
    def __init__(self):
        '''Initialize StepExtractor class.'''
        self.dbal = {} # Dictionary-based adjacency list for directory steps (dbal)

    def edgify(self, parent, child):
        '''Create a directed edge in the adjacency list.'''
        if parent not in self.dbal:
            self.dbal[parent] = set()
        self.dbal[parent].add(child)

    def extract(self):
        '''
        Extract directory steps from files paths stored in the filepath table.
        Constructs a dictionary-based adjacency list for directory steps (dbal) and saves it.
        '''
        # Fetch file paths from the database
        filepaths = fetch(columns=['filepath'], table_title='filepaths')
        print(f"Fetched filepaths: {filepaths}")  # Debug print

        # Build the dbal adjacency list
        for filepath_tuple in filepaths:
            filepath_id = filepath_tuple[0]
            filepath = filepath_tuple[0]
            steps = pathextract(filepath).split(os.path.sep)
            print(f"Extracted steps for filepath {filepath}: {steps}")  # Debug print
            
            # Construct the dbal adjacency list from path segments
            for i in range(len(steps)-1):
                parent = steps[i]
                child = steps[i + 1]
                print(f"Adding edge from {parent} to {child}")  # Debug print
                self.edgify(parent, child)

            # Save the dbal adjacency list to the database (filesteps table)
            self.savesteps(filepath_id)
            self.dbal.clear()  # Clear the dbal for the next file

        print("DBAL saved to database")  # Debug print

    def savesteps(self, filepath_id):
        """
        Save the dbal adjacency list to the database (filesteps table).
        
        :param filepath_id: The ID of the filepath
        """
        # Connect to database
        conn = sqlite3.connect('../classified.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute(f"CREATE TABLE IF NOT EXISTS filesteps (filepath_id TEXT, parent TEXT, child TEXT, UNIQUE(filepath_id, parent, child))")
        
        # Insert values into table
        for parent, children in self.dbal.items():
            for child in children:
                query = "INSERT OR IGNORE INTO filesteps (filepath_id, parent, child) VALUES (?, ?, ?)"
                values = (filepath_id, parent, child)
                print(f"Executing query: {query} with values: {values}")  # Debug print
                c.execute(query, values)
        
        # Commit changes
        conn.commit()
        
        # Close connection
        conn.close()
        print("Data saved to filesteps table")  # Debug print


# Since we have database path set to '../classified.db', we can initialize the StepExtractor class
# and extract the directory steps from the file paths in the filepaths table.

# Initialize StepExtractor class
stepextractor = StepExtractor()

# Extract directory steps from file paths
stepextractor.extract()
# The directory steps are extracted from the file paths and saved to the filesteps table in the classified.db database.