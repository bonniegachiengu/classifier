import os
import re
import sqlite3

# Define utility functions

# Function to extract the filename from a path
def filenaming(path):
    """Return the filename of a path."""
    return os.path.basename(path)


# Function to remove the filename from a path
def pathextract(path):
    """Return the path of a path after removing the filename."""
    return os.path.normpath(os.path.dirname(path))


# Define pathconstruct function to extract the path of a file from its root and filename
def pathconstruct(root, filename):
    """
    Extract the path of a file from its root and filename, or dir.
    
    The pathconstruct function takes the root directory and filename of a file as arguments, 
    and returns the full path of the file.
    
    :param root: Root directory
    :param filename: Filename
    :return: Full path of the file
    """
    
    # get filename from filenaming function in utils module
    filename = filenaming(filename)

    # Return full path
    return os.path.join(root, filename)


def titlextract(filename):
    '''
    titlextract.py is a module that provides a function for extracting the title of a file from its name.

    The titlextract function takes a file name as an argument and returns the title of the file. 
    The title is extracted by changing filenames with this format "Duck.Duck.Goose.2018.720p.BluRay.x264-[YTS.AM].mp4" to
    "Duck Duck Goose".

    The titlextract function is used by the PathFinder class in the pathfinder module to extract the title of a file from its name.
    '''

    # Remove file extension
    filename = filenaming(filename)
    filename = filename.split('.')[0:-1] # Remove file extension

    # Extract title up to year
    title = [] # Initialize title list
    for word in filename:
        if word.isnumeric() and len(word) == 4:
            break
        title.append(word)

    # Join title words
    title = ' '.join(title)

    return title


# Function to extract the year from a filename
def yearextract(filename):
    '''
    yearextract.py is a module that provides a function for extracting the year of a file from its name.

    The yearextract function takes a file name as an argument and returns the year of the file. 
    The year is extracted by changing filenames with this format "Duck.Duck.Goose.2018.720p.BluRay.x264-[YTS.AM].mp4" to
    "2018".
    '''
    # Remove file extension
    filename = filenaming(filename)
    filename = filename.split('.')[0:-1] # Remove file extension

    # Extract year using regex
    year = None
    match = re.search(r'(19\d{2}|20\d{2})', '.'.join(filename))
    if match:
        year = match.group(0)

    return year


# Function to extract the resolution from a filename
def resextract(filename):
    '''
    resolutionextract.py is a module that provides a function for extracting the resolution of a file from its name.

    The resolutionextract function takes a file name as an argument and returns the resolution of the file. 
    The resolution is extracted by changing filenames with this format "Duck.Duck.Goose.2018.720p.BluRay
    .x264-[YTS.AM].mp4" to "720p".
    '''
    # Remove file extension
    filename = filenaming(filename)
    filename = filename.split('.')[0:-1] # Remove file extension

    # Extract resolution using regex
    resolution = None
    match = re.search(r'(\d{3,4}p)', '.'.join(filename))
    if match:
        resolution = match.group(0)

    return resolution


# Function to extract the codec from a filename
def codecextract(filename):
    '''
    codecextract.py is a module that provides a function for extracting the codec of a file from its name.

    The codecextract function takes a file name as an argument and returns the codec of the file. 
    The codec is extracted by changing filenames with this format "Duck.Duck.Goose.2018.720p.BluRay.x264-[YTS.AM].mp4" to
    "x264".
    '''
    # Remove file extension
    filename = filenaming(filename)
    filename = filename.split('.')[0:-1] # Remove file extension

    # Extract codec using regex
    codec = None
    match = re.search(r'x264|x265|XviD|DivX', '.'.join(filename))
    if match:
        codec = match.group(0)

    return codec


# Function to save data to a sqlite3 database
def save(columns, values, table_title):
    """
    Save data to a sqlite3 database.
    
    The save function takes a list of columns, a list of values, and a table title as arguments, 
    and saves the data to a sqlite3 database called classified.db.
    
    :param columns: List of column names
    :param values: List of tuples, where each tuple contains values for the columns
    :param table_title: Table title
    """
    
    # Add 'id' column for autoincrement primary key
    columns = ['id'] + columns
    
    # Connect to database
    conn = sqlite3.connect('../classified.db')
    c = conn.cursor()
    
    # Create table if not exists
    c.execute(f"CREATE TABLE IF NOT EXISTS {table_title} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(columns[1:])}, UNIQUE({', '.join(columns[1:])}))")
    
    # Insert values into table
    for value in values:
        if len(value) != len(columns) - 1:
            raise ValueError(f"Incorrect number of values supplied for columns {columns[1:]}. Expected {len(columns) - 1}, got {len(value)}.")
        query = f"INSERT OR IGNORE INTO {table_title} ({', '.join(columns[1:])}) VALUES ({', '.join(['?']*len(columns[1:]))})"
        c.execute(query, value)
    
    # Commit changes
    conn.commit()
    
    # Close connection
    conn.close()


# Function to fetch data from a sqlite3 database
def fetch(columns, table_title):
    """
    Fetch data from a sqlite3 database.
    
    The fetch function takes a list of columns and a table title as arguments, 
    and fetches the data from a sqlite3 database called classified.db.
    
    :param columns: List of column names
    :param table_title: Table title
    :return: List of data
    """
    
    # Connect to database
    conn = sqlite3.connect('../classified.db')
    c = conn.cursor()
    
    # Fetch data from table
    c.execute(f"SELECT {', '.join(columns)} FROM {table_title}")
    data = c.fetchall()
    
    # Close connection
    conn.close()
    
    return data