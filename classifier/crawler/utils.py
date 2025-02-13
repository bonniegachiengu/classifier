import sqlite3

# Define Crawler utility functions

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