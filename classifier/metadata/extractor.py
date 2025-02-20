import sqlite3
import subprocess
import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(filename='extract.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Extractor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_merged_metadata_table()

    def _connect(self):
        """Establish a database connection."""
        return sqlite3.connect(self.db_path)

    def _ensure_merged_metadata_table(self):
        """Ensure merged_metadata table exists with the correct structure."""
        query = """
        CREATE TABLE IF NOT EXISTS merged_metadata (
            file_id INTEGER PRIMARY KEY,
            filepath TEXT NOT NULL,
            filename TEXT NOT NULL,
            title TEXT,
            year TEXT,
            resolution TEXT,
            codec TEXT,
            imdbID TEXT,
            rottenTomatoes TEXT,
            rated TEXT,
            released TEXT,
            runtime TEXT,
            writer TEXT,
            plot TEXT,
            language TEXT,
            country TEXT,
            awards TEXT,
            poster TEXT,
            imdbRating TEXT,
            imdbVotes TEXT,
            type TEXT,
            boxOffice TEXT,
            FOREIGN KEY (file_id) REFERENCES filepaths(id)
        )
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()

    def fetch_existing_metadata(self) -> List[Dict[str, Any]]:
        """Fetches metadata from classified.db for merging."""
        query = """
        SELECT 
            f.id AS file_id, 
            f.filepath, 
            f.filename,
            m.title, 
            m.year, 
            d.resolution, 
            d.codec,  -- Fetch codec from filedetails
            m.imdbID,
            m.rottenTomatoes,
            m.rated,
            m.released,
            m.runtime,
            m.writer,
            m.plot,
            m.language,
            m.country,
            m.awards,
            m.poster,
            m.imdbRating,
            m.imdbVotes,
            m.type,
            m.boxOffice
        FROM filepaths f
        LEFT JOIN filemetadata m ON f.id = m.file_id
        LEFT JOIN filedetails d ON f.id = d.file_id
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        columns = [
            "file_id", "filepath", "filename", "title", "year", "resolution", "codec", 
            "imdbID", "rottenTomatoes", "rated", "released", "runtime", "writer", "plot",
            "language", "country", "awards", "poster", "imdbRating", "imdbVotes", "type", "boxOffice"
        ]
        return [dict(zip(columns, row)) for row in rows]

    def update_filedetails(self, file_id: int, codec: str):
        """Updates the filedetails table with extracted codec information."""
        query = """
        UPDATE filedetails
        SET codec = ?
        WHERE file_id = ?
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (codec, file_id))
            conn.commit()

    def insert_merged_metadata(self, metadata: List[Dict[str, Any]]):
        """Inserts or updates metadata into merged_metadata."""
        query = """
        INSERT INTO merged_metadata (
            file_id, filepath, filename, title, year, resolution, codec, 
            imdbID, rottenTomatoes, rated, released, runtime, writer, plot, 
            language, country, awards, poster, imdbRating, imdbVotes, type, boxOffice
        ) VALUES (
            :file_id, :filepath, :filename, :title, :year, :resolution, :codec, 
            :imdbID, :rottenTomatoes, :rated, :released, :runtime, :writer, :plot, 
            :language, :country, :awards, :poster, :imdbRating, :imdbVotes, :type, :boxOffice
        )
        ON CONFLICT(file_id) DO UPDATE SET 
            filepath=excluded.filepath,
            filename=excluded.filename,
            title=excluded.title,
            year=excluded.year,
            resolution=excluded.resolution,
            codec=excluded.codec,
            imdbID=excluded.imdbID,
            rottenTomatoes=excluded.rottenTomatoes,
            rated=excluded.rated,
            released=excluded.released,
            runtime=excluded.runtime,
            writer=excluded.writer,
            plot=excluded.plot,
            language=excluded.language,
            country=excluded.country,
            awards=excluded.awards,
            poster=excluded.poster,
            imdbRating=excluded.imdbRating,
            imdbVotes=excluded.imdbVotes,
            type=excluded.type,
            boxOffice=excluded.boxOffice
        """
        # Ensure all keys are present in each metadata dictionary
        for entry in metadata:
            for key in ["file_id", "filepath", "filename", "title", "year", "resolution", "codec", 
                        "imdbID", "rottenTomatoes", "rated", "released", "runtime", "writer", "plot", 
                        "language", "country", "awards", "poster", "imdbRating", "imdbVotes", "type", "boxOffice"]:
                if key not in entry:
                    entry[key] = None

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, metadata)
            conn.commit()

    def run_extraction(self):
        """Main function to fetch and merge metadata into the new table."""
        metadata = self.fetch_existing_metadata()

        # Insert into merged_metadata
        self.insert_merged_metadata(metadata)
        logging.info("Metadata extraction and merging completed successfully.")

# Usage example
if __name__ == "__main__":
    extractor = Extractor("../classified.db")
    extractor.run_extraction()
