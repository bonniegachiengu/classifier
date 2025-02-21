import sqlite3
import json
from collections import defaultdict
import re
import logging

class SortingHat:
    def __init__(self, DBPATH="../classified.db"):
        self.dbpath = DBPATH
        self.dag = self.buildDAG()
        self.filemetadata = self.loadFileMetadata()
        self.classifications = {}
        self.genres, self.studios = self.extractGenres()  # Ensure genres are stored in the database

    def buildDAG(self):
        """Generates a DAG JSON dynamically from the filesteps table."""
        dag = defaultdict(list)
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT parent, child FROM filesteps")
            for parent, child in cursor.fetchall():
                if child not in dag[parent]:
                    dag[parent].append(child)
        return dict(dag)

    def loadFileMetadata(self):
        """Loads metadata from the database."""
        filemetadata = {}
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_id, title, year, genre, type FROM filemetadata")
            for file_id, title, year, genre, media_type in cursor.fetchall():
                filemetadata[file_id] = {"title": title, "year": year, "genre": genre, "type": media_type}
        return filemetadata

    def extractGenres(self):
        """Extracts unique genres and studios from filemetadata and stores them in the genre table."""
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
        
        return genres, studios

    def extractAncestryGenres(self, folder):
        """Extracts genres from ancestor folders."""
        genres = set()
        to_remove = {"E:", "Films", "Media", "Series", "Movies"}  # Types to exclude

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
        return genres

    def analyzeStructure(self, genres, studios):
        """
        Analyzes DAG Structure after filtering unwanted categories and extracting genres to extract movies so that we remain with franchises
        """
        filtered_dag = self.filterDAG()
        logging.info("Filtered DAG: %s", filtered_dag)  # Log statement

        new_genres = set()

        # Classify parents
        for parent, children in filtered_dag.items():
            if self.isMovie(parent, children):
                self.classifications[parent] = 'Movie'
                logging.info("Classified %s as Movie", parent)  # Log statement
            elif self.isFranchise(parent, children):
                self.classifications[parent] = 'Franchise'
                logging.info("Classified %s as Franchise", parent)  # Log statement
            else:
                new_genres.add(parent)

        # Classify children
        for parent, children in filtered_dag.items():
            for child in children:
                if child not in self.classifications:
                    if self.isMovie(child, []):
                        self.classifications[child] = 'Movie'
                        logging.info("Classified %s as Movie", child)  # Log statement

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

    def filterDAG(self):
        """Removes unwanted categories like root folders, types, genres, and studios."""
        to_remove = {"E:", "Films", "Media", "Series", "Movies"}  # Types
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM genre")
            to_remove.update(row[0] for row in cursor.fetchall())  # Add genres to remove
        
        return {k: v for k, v in self.dag.items() if k not in to_remove}

    def isFranchise(self, parent, children):
        """Checks if all children are classified as movies."""
        for child in children:
            if not self.isMovie(child, self.dag.get(child, [])):
                logging.info("%s is not a franchise because %s is not a movie", parent, child)  # Log statement
                return False
        logging.info("%s is a franchise", parent)  # Log statement
        return True

    def isMovie(self, parent, children):
        """Checks if a folder name has a year in it, i.e. in Hancock (2008)."""
        if re.search(r"\(\d{4}\)", parent):
            logging.info("%s is a movie", parent)  # Log statement
            return True
        logging.info("%s is not a movie", parent)  # Log statement
        return False
        

    def saveClassifications(self):
        """Saves classification results to the classifications table."""
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    folder TEXT PRIMARY KEY, 
                    type TEXT,
                    classes TEXT,
                    levels TEXT,
                    genre TEXT,
                    FOREIGN KEY (folder) REFERENCES filesteps(parent)
                )
            """)
            for folder, type in self.classifications.items():
                if type == 'Movie':
                    classes = 'Film'
                    levels = 'Release'
                    genre = self.filemetadata[folder]['genre']
                    logging.info("Saving %s as Movie with classes: %s, levels: %s, genre: %s", folder, classes, levels, genre)  # Log statement
                elif type == 'Franchise':
                    classes = 'Franchise'
                    levels = 'Playlist'
                    genre = self.filemetadata[folder]['genre']
                    logging.info("Saving %s as Franchise with classes: %s, levels: %s, genre: %s", folder, classes, levels, genre)  # Log statement
                else:
                    logging.info("Skipping %s with classification: %s", folder, type)  # Log statement
                    continue
                cursor.execute("INSERT OR REPLACE INTO classifications (folder, type, classes, levels, genre) VALUES (?, ?, ?, ?, ?)", 
                               (folder, type, classes, levels, genre))
            conn.commit()
        logging.info("Classes saved to database.")  # Log statement

    def saveType(self):
        """Saves type to a new table in the database."""
        logging.info("Type results: %s", self.classifications)  # Log classification results
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
                logging.info("Saving %s with classification: %s", folder, type)  # Log statement
                cursor.execute("INSERT OR REPLACE INTO type (folder, type) VALUES (?, ?)", (folder, type))
            conn.commit()
        logging.info("Types saved to database.")  # Log statement
        self.saveClassifications()  # Save to classifications table

    def classify(self):
        """Runs the full classification pipeline."""
        self.analyzeStructure(self.genres, self.studios)
        self.saveType()
        return self.classifications

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(filename='sortinghat.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    sorter = SortingHat()
    classifications = sorter.classify()
    
    # Save DAG to a JSON file
    with open('dag.json', 'w') as f:
        json.dump(sorter.dag, f, indent=4)
    
    logging.info("DAG saved to dag.json")
    
    # Verify database entries
    with sqlite3.connect(sorter.dbpath) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM classifications")
        rows = cursor.fetchall()
        logging.info("Database entries in classifications table: %s", rows)
