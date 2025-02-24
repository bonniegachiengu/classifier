import sqlite3
import json
from collections import defaultdict
import re
from classifier.utils.logger import log_info, log_debug, log_warning, log_error
from classifier.utils.config import DB_PATH, EXCLUDED_FOLDERS

class SortingHat:
    """
    The SortingHat class is responsible for classifying folders into movies and franchises
    based on their metadata and structure in the database.

    Attributes:
        dbpath (str): Path to the SQLite database.
        dag (dict): A dictionary representing the Directed Acyclic Graph (DAG) of the filesteps table.
        filemetadata (dict): A dictionary where keys are file IDs and values are dictionaries containing file metadata.
        classifications (dict): A dictionary where keys are folder names and values are their classifications.
        genres (set): A set of unique genres extracted from the filemetadata table.
        studios (set): A set of studios to filter out.
    """

    def __init__(self, DBPATH=DB_PATH):
        """
        Initializes the SortingHat instance.

        Args:
            DBPATH (str): Path to the SQLite database.
        """
        self.dbpath = DBPATH
        self.dag = self.buildDAG()
        self.filemetadata = self.loadFileMetadata()
        self.classifications = {}
        self.genres, self.studios = self.extractGenres()  # Ensure genres are stored in the database
        log_info("Initialized SortingHat with DB path: %s", DBPATH)

    def buildDAG(self):
        """
        Generates a Directed Acyclic Graph (DAG) JSON dynamically from the filesteps table.

        Returns:
            dict: A dictionary representing the DAG where keys are parent nodes and values are lists of child nodes.
        """
        log_info("Building DAG from filesteps table")
        dag = defaultdict(list)
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT parent, child FROM filesteps")
            for parent, child in cursor.fetchall():
                if child not in dag[parent]:
                    dag[parent].append(child)
        log_info("DAG built: %s", dag)
        return dict(dag)

    def loadFileMetadata(self):
        """
        Loads metadata from the database.

        Returns:
            dict: A dictionary where keys are file IDs and values are dictionaries containing file metadata.
        """
        log_info("Loading file metadata from database")
        filemetadata = {}
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, title, year, genre, type FROM filemetadata")
            for file_id, title, year, genre, media_type in cursor.fetchall():
                filemetadata[file_id] = {"title": title, "year": year, "genre": genre, "type": media_type}
        log_info("File metadata loaded: %s", filemetadata)
        return filemetadata

    def extractGenres(self):
        """
        Extracts unique genres and studios from filemetadata and stores them in the genre table.

        Returns:
            tuple: A set of unique genres and a set of studios to filter out.
        """
        log_info("Extracting unique genres and studios from filemetadata")
        genres = set()
        studios = {"DC", "Marvel"}  # Studios we want to filter out

        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS genre (name TEXT PRIMARY KEY)")
            cursor.execute("SELECT DISTINCT genre FROM filemetadata")
            for row in cursor.fetchall():
                if row[0]:
                    for g in row[0].split(','):
                        g = g.strip().title()
                        if g and g not in studios:
                            genres.add(g)
            
            for genre in genres:
                cursor.execute("INSERT OR IGNORE INTO genre (name) VALUES (?)", (genre,))
            conn.commit()
        
        log_info("Genres extracted: %s", genres)
        return genres, studios

    def extractAncestryGenres(self, folder):
        """
        Extracts genres from ancestor folders.

        Args:
            folder (str): The folder for which to extract ancestor genres.

        Returns:
            set: A set of genres extracted from ancestor folders.
        """
        log_info("Extracting genres from ancestor folders for: %s", folder)
        genres = set()
        to_remove = EXCLUDED_FOLDERS  # Types to exclude

        def getAncestors(folder):
            ancestors = []
            with sqlite3.connect(self.dbpath) as conn:
                cursor = conn.cursor()
                while folder:
                    cursor.execute("SELECT parent FROM filesteps WHERE child = ?", (folder,))
                    result = cursor.fetchone()
                    if result and result[0] not in to_remove:
                        ancestors.append(result[0])
                        folder = result[0]
                    else:
                        break
            return ancestors

        ancestors = getAncestors(folder)
        for ancestor in ancestors:
            if ancestor not in to_remove and self.classifications.get(ancestor) != 'Franchise':
                genres.add(ancestor)
        log_info("Ancestry genres extracted: %s", genres)
        return genres

    def analyzeStructure(self, genres, studios):
        """
        Analyzes DAG Structure after filtering unwanted categories and extracting genres to extract movies so that we remain with franchises.

        Args:
            genres (set): A set of unique genres.
            studios (set): A set of studios to filter out.
        """
        log_info("Analyzing DAG structure")
        filtered_dag = self.filterDAG()
        log_info("Filtered DAG: %s", filtered_dag)  # Log statement

        new_genres = set()

        # Classify parents
        for parent, children in filtered_dag.items():
            if self.isMovie(parent, children):
                self.classifications[parent] = 'Movie'
                log_info("Classified %s as Movie", parent)  # Log statement
            elif self.isFranchise(parent, children):
                self.classifications[parent] = 'Franchise'
                log_info("Classified %s as Franchise", parent)  # Log statement
            else:
                new_genres.add(parent)

        # Classify children
        for parent, children in filtered_dag.items():
            for child in children:
                if child not in self.classifications:
                    if self.isMovie(child, []):
                        self.classifications[child] = 'Movie'
                        log_info("Classified %s as Movie", child)  # Log statement

    # Add new genres to the genre table
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            for genre in new_genres:
                if genre not in genres and genre not in studios:
                    cursor.execute("INSERT OR IGNORE INTO genre (name) VALUES (?)", (genre,))
            conn.commit()

    # Extract and store genres for each classified folder
        for folder in self.classifications:
            if self.classifications[folder] == 'Movie':
                ancestry_genres = self.extractAncestryGenres(folder)
                cursor.execute("SELECT filepath_id FROM filesteps WHERE child = ?", (folder,))
                filepath_id_result = cursor.fetchone()
                if filepath_id_result:
                    filepath_id = filepath_id_result[0]
                    cursor.execute("SELECT filetitle FROM filepaths WHERE id = ?", (filepath_id,))
                    filetitle = cursor.fetchone()
                    if filetitle:
                        cursor.execute("SELECT genre FROM filemetadata WHERE title = ?", (filetitle[0],))
                        result = cursor.fetchone()
                        if result:
                            file_genres = set(result[0].split(','))
                            ancestry_genres.update(file_genres)
                            self.filemetadata[folder] = {'genre': ', '.join(ancestry_genres)}
            elif self.classifications[folder] == 'Franchise':
                franchise_genres = set()
                for child in filtered_dag.get(folder, []):
                    if self.classifications.get(child) == 'Movie':
                        cursor.execute("SELECT filepath_id FROM filesteps WHERE child = ?", (child,))
                        filepath_id_result = cursor.fetchone()
                        if filepath_id_result:
                            filepath_id = filepath_id_result[0]
                            cursor.execute("SELECT filetitle FROM filepaths WHERE id = ?", (filepath_id,))
                            filetitle = cursor.fetchone()
                            if filetitle:
                                cursor.execute("SELECT genre FROM filemetadata WHERE title = ?", (filetitle[0],))
                                result = cursor.fetchone()
                            if result:
                                franchise_genres.update(result[0].split(','))
                self.filemetadata[folder] = {'genre': ', '.join(franchise_genres)}
        log_info("Genres stored for classified folders")

    def filterDAG(self):
        """
        Removes unwanted categories like root folders, types, genres, and studios.

        Returns:
            dict: A filtered DAG dictionary.
        """
        log_info("Filtering DAG to remove unwanted categories")
        to_remove = {"E:", "Films", "Media", "Series", "Movies"}  # Types
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM genre")
            to_remove.update(row[0] for row in cursor.fetchall())  # Add genres to remove
        
        filtered_dag = {k: v for k, v in self.dag.items() if k not in to_remove} # Filter out unwanted categories
        log_info("Filtered DAG: %s", filtered_dag)
        return filtered_dag

    def isFranchise(self, parent, children):
        """
        Checks if all children are classified as movies.

        Args:
            parent (str): The parent folder.
            children (list): A list of child folders.

        Returns:
            bool: True if all children are movies, False otherwise.
        """
        log_info("Checking if %s is a franchise", parent)
        for child in children:
            if not self.isMovie(child, self.dag.get(child, [])):
                log_info("%s is not a franchise because %s is not a movie", parent, child)  # Log statement
                return False
        log_info("%s is a franchise", parent)  # Log statement
        return True

    def isMovie(self, parent, children):
        """
        Checks if a folder name has a year in it, i.e. in Hancock (2008).

        Args:
            parent (str): The parent folder.
            children (list): A list of child folders.

        Returns:
            bool: True if the folder name has a year in it, False otherwise.
        """
        log_info("Checking if %s is a movie", parent)
        if re.search(r"\(\d{4}\)", parent):
            log_info("%s is a movie", parent)  # Log statement
            return True
        log_info("%s is not a movie", parent)  # Log statement
        return False

    def saveClassifications(self):
        """
        Saves classification results to the classifications table.
        """
        log_info("Saving classification results to the database")
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    file_id INTEGER,
                    folder TEXT PRIMARY KEY, 
                    type TEXT,
                    classes TEXT,
                    levels TEXT,
                    genre TEXT,
                    FOREIGN KEY (file_id) REFERENCES filesteps(filepath_id),
                    FOREIGN KEY (folder) REFERENCES filesteps(parent)
                )
            """)
            for folder, type in self.classifications.items():
                if type == 'Movie':
                    classes = 'Film'
                    levels = 'Release'
                    genre = ', '.join(sorted(set(g.strip() for g in self.filemetadata.get(folder, {}).get('genre', '').split(','))))  # Remove duplicates and strip whitespace
                    log_info("Saving %s as Movie with classes: %s, levels: %s, genre: %s", folder, classes, levels, genre)  # Log statement
                elif type == 'Franchise':
                    classes = 'Franchise'
                    levels = 'Playlist'
                    genre = ', '.join(sorted(set(g.strip() for g in self.filemetadata.get(folder, {}).get('genre', '').split(','))))  # Remove duplicates and strip whitespace
                    log_info("Saving %s as Franchise with classes: %s, levels: %s, genre: %s", folder, classes, levels, genre)  # Log statement
                else:
                    log_info("Skipping %s with classification: %s", folder, type)  # Log statement
                    continue
                
                # Fetch the file_id from the filesteps table
                cursor.execute("SELECT filepath_id FROM filesteps WHERE parent = ? OR child = ?", (folder, folder))
                file_id_result = cursor.fetchone()
                file_id = file_id_result[0] if file_id_result else None
                
                cursor.execute("INSERT OR REPLACE INTO classifications (file_id, folder, type, classes, levels, genre) VALUES (?, ?, ?, ?, ?, ?)", 
                               (file_id, folder, type, classes, levels, genre))
            conn.commit()
        log_info("Classes saved to database.")  # Log statement

    def saveType(self):
        """
        Saves type to a new table in the database.
        """
        log_info("Saving type results to the database")
        log_info("Type results: %s", self.classifications)  # Log classification results
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS type (
                    folder TEXT PRIMARY KEY, 
                    type TEXT,
                    FOREIGN KEY (folder) REFERENCES filesteps(parent)
                )
            """)
            for folder, type in self.classifications.items():
                log_info("Saving %s with classification: %s", folder, type)  # Log statement
                cursor.execute("INSERT OR REPLACE INTO type (folder, type) VALUES (?, ?)", (folder, type))
            conn.commit()
        log_info("Types saved to database.")  # Log statement
        self.saveClassifications()  # Save to classifications table

    def classify(self):
        """
        Runs the full classification pipeline.

        Returns:
            dict: A dictionary of classifications where keys are folder names and values are their classifications.
        """
        log_info("Running the full classification pipeline")
        self.analyzeStructure(self.genres, self.studios)
        self.saveType()
        log_info("Classification results: %s", self.classifications)
        return self.classifications

if __name__ == "__main__":
    # Setup logging
    log_info("Starting SortingHat...")  # Log statement
    
    sorter = SortingHat()
    classifications = sorter.classify()
    
    # Save DAG to a JSON file
    with open('../dag.json', 'w') as f:
        json.dump(sorter.dag, f, indent=4)
    
    log_info("DAG saved to ../dag.json")
    
    # Verify database entries
    with sqlite3.connect(sorter.dbpath) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classifications")
        rows = cursor.fetchall()
        log_info("Database entries in classifications table: %s", rows)
