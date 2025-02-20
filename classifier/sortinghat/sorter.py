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

    def analyzeStructure(self, genres, studios):
        """
        Analyzes DAG Structure after filtering unwanted categories and extracting genres to extract movies so that we remain with franchises
        """
        filtered_dag = self.filterDAG()
        logging.info("Filtered DAG: %s", filtered_dag)  # Log statement

        new_genres = set()

        for parent, child in filtered_dag.items():
            if self.isMovie(parent, child):
                self.classifications[child] = 'Movie'
                logging.info("Classified %s as Movie", child)  # Log statement
            elif self.isFranchise(parent, child):
                self.classifications[parent] = 'Franchise'
                logging.info("Classified %s as Franchise", parent)  # Log statement
            else:
                new_genres.add(parent)

        # Add new genres to the genre table
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            for genre in new_genres:
                if genre not in genres and genre not in studios:
                    cursor.execute("INSERT OR IGNORE INTO genre (name) VALUES (?)", (genre,))
            conn.commit()

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
            if not self.isMovie(child, []):
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
        

    def saveResults(self):
        """Saves classification results to a new table in the database."""
        with sqlite3.connect(self.dbpath) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classifications (
                    folder TEXT PRIMARY KEY, 
                    classification TEXT,
                    FOREIGN KEY (folder) REFERENCES filesteps(parent)
                )
            """)
            for folder, classification in self.classifications.items():
                cursor.execute("INSERT OR REPLACE INTO classifications (folder, classification) VALUES (?, ?)", (folder, classification))
            conn.commit()
        logging.info("Classifications saved to database.")  # Log statement

    def classify(self):
        """Runs the full classification pipeline."""
        self.analyzeStructure(self.genres, self.studios)
        self.saveResults()
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
