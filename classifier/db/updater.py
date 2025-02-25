import sqlite3
from classifier.utils.config import DB_PATH

def find_missing_files(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query to get file details
    cursor.execute("SELECT file_id, title, year FROM filedetails")
    file_details = cursor.fetchall()

    # Query to get file metadata
    cursor.execute("SELECT file_id FROM filemetadata")
    file_metadata = cursor.fetchall()

    # Convert metadata to a set for faster lookup
    metadata_set = set(file_id[0] for file_id in file_metadata)

    # Find missing files
    missing_files = [file for file in file_details if file[0] not in metadata_set]

    # Write missing files to ../missing.txt
    with open('../missing_movies.txt', 'w') as f:
        for file in missing_files:
            f.write(f"{file[1]}, {file[2]}\n")

    conn.close()

def find_missing_people(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    missing_people = []

    # Check actors table
    cursor.execute("SELECT name FROM actors WHERE name IS NULL OR name = 'N/A' OR avatar IS NULL OR avatar = 'N/A' OR bio IS NULL OR bio = 'N/A'")
    missing_actors = cursor.fetchall()
    for actor in missing_actors:
        missing_people.append((actor[0], 'actor'))

    # Check writers table
    cursor.execute("SELECT name FROM writers WHERE name IS NULL OR name = 'N/A' OR avatar IS NULL OR avatar = 'N/A' OR bio IS NULL OR bio = 'N/A'")
    missing_writers = cursor.fetchall()
    for writer in missing_writers:
        missing_people.append((writer[0], 'writer'))

    # Check directors table
    cursor.execute("SELECT name FROM directors WHERE name IS NULL OR name = 'N/A' OR avatar IS NULL OR avatar = 'N/A' OR bio IS NULL OR bio = 'N/A'")
    missing_directors = cursor.fetchall()
    for director in missing_directors:
        missing_people.append((director[0], 'director'))

    # Write missing people to ../missing_people.txt
    with open('../missing_people.txt', 'w') as f:
        for name, person_type in missing_people:
            f.write(f"{name}, {person_type}\n")

    conn.close()
