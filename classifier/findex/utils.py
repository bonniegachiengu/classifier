import os
import sqlite3

def filenamer(path):
    """Return the filename of a path."""
    return os.path.basename(path)

def pathextractor(root, filename):
    """
    Extract the path of a file from its root and filename, or dir.
    
    The pathextractor function takes the root directory and filename of a file as arguments, 
    and returns the full path of the file.
    
    :param root: Root directory
    :param filename: Filename
    :return: Full path of the file
    """
    
    # get filename from filenamer function in utils module
    filename = filenamer(filename)

    # Return full path
    return os.path.join(root, filename)

def save_to_db(columns, values, table_title):
    """
    Save data to a sqlite3 database.
    
    The save_to_db function takes a list of columns, a list of values, and a table title as arguments, 
    and saves the data to a sqlite3 database called classified.db.
    
    :param columns: List of column names
    :param values: List of values
    :param table_title: Table title
    """
    
    # Connect to database
    conn = sqlite3.connect('classified.db')
    c = conn.cursor()
    
    # Create table if not exists
    c.execute(f"CREATE TABLE IF NOT EXISTS {table_title} ({', '.join(columns)}, UNIQUE({', '.join(columns)}))")
    
    # Check if the entry already exists
    query = f"SELECT COUNT(*) FROM {table_title} WHERE " + " AND ".join([f"{col}=?" for col in columns])
    c.execute(query, values)
    if c.fetchone()[0] == 0:
        # Insert values into table
        c.execute(f"INSERT INTO {table_title} ({', '.join(columns)}) VALUES ({', '.join(['?']*len(values))})", values)
    
    # Commit changes
    conn.commit()
    
    # Close connection
    conn.close()