import sqlite3
from classifier.utils.config import DB_PATH
from .augmentor import MetAugment


class MetAssembly:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.cursor = self.db.cursor()

    def fetchType(self):
        """
        Fetches and processes types from the filemetadata and classifications tables.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Process movies from filemetadata
            cursor.execute("SELECT * FROM filemetadata")
            for record in cursor.fetchall():
                if record['type'] == 'movie':
                    self.assembleMovies(record)
            
            # Process franchises from classifications
            cursor.execute("SELECT * FROM classifications WHERE type = 'franchise'")
            for record in cursor.fetchall():
                self.assembleFranchises(record)

    def assembleMovies(self, movieRecord):
        """
        Processes a movie record and inserts it into the movieassemble table.

        Args:
            movieRecord (dict): A dictionary containing movie metadata.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create movieassemble table if it does not exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS movieassemble (
                    id INTEGER PRIMARY KEY,
                    path TEXT,
                    folder TEXT,
                    filename TEXT,
                    imdbID TEXT,
                    title TEXT,
                    year INTEGER,
                    resolution TEXT,
                    codec TEXT,
                    level TEXT,
                    class TEXT,
                    type TEXT,
                    franchise TEXT,
                    genres TEXT,
                    rated TEXT,
                    released TEXT,
                    runtime TEXT,
                    director TEXT,
                    writers TEXT,
                    cast TEXT,
                    plot TEXT,
                    languages TEXT,
                    countries TEXT,
                    awards TEXT,
                    poster TEXT,
                    imdbRating REAL,
                    imdbVotes INTEGER,
                    rottenTomatoes TEXT,
                    boxOffice TEXT
                )
            """)
            
            # Augment franchise information
            augmented_franchise = MetAugment.amberAlert(movieRecord)
            
            # Insert movie record into movieassemble table
            cursor.execute("""
                INSERT INTO movieassemble (
                    id, path, folder, filename, imdbID, title, year, resolution, codec, level,
                    class, type, franchise, genres, rated, released, runtime, director, writers,
                    cast, plot, languages, countries, awards, poster, imdbRating, imdbVotes,
                    rottenTomatoes, boxOffice
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                movieRecord['filepaths']['id'], 
                movieRecord['filepaths']['filepath'],
                movieRecord['classifications']['folder'],
                movieRecord['filepaths']['filename'],
                movieRecord['filemetadata']['imdbID'],
                movieRecord['filedetails']['title'],
                movieRecord['filedetails']['year'],
                movieRecord['filedetails']['resolution'],
                movieRecord['filedetails']['codec'],
                movieRecord['classifications']['levels'],
                movieRecord['classifications']['classes'],
                movieRecord['classifications']['type'],
                augmented_franchise if augmented_franchise else None,
                movieRecord['classifications']['genre'],
                movieRecord['filemetadata']['rated'],
                movieRecord['filemetadata']['released'],
                movieRecord['filemetadata']['runtime'],
                movieRecord['filemetadata']['director'],
                movieRecord['filemetadata']['writer'],
                movieRecord['filemetadata']['actors'],
                movieRecord['filemetadata']['plot'],
                movieRecord['filemetadata']['language'],
                movieRecord['filemetadata']['country'],
                movieRecord['filemetadata']['awards'],
                movieRecord['filemetadata']['poster'],
                movieRecord['filemetadata']['imdbRating'],
                movieRecord['filemetadata']['imdbVotes'],
                movieRecord['filemetadata']['rottenTomatoes'],
                movieRecord['filemetadata']['boxOffice']
            ))
            conn.commit()

    def assembleFranchises(self, franchiseRecord):
        """
        Processes a franchise record and inserts it into the franchiseassemble table.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create franchiseassemble table if it does not exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS franchiseassemble (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT,
                    folder TEXT,
                    title TEXT,
                    year INTEGER,
                    level TEXT,
                    class TEXT,
                    type TEXT,
                    genres TEXT,
                    rated TEXT,
                    released TEXT,
                    runtime INTEGER,
                    director TEXT,
                    writers TEXT,
                    cast TEXT,
                    plot TEXT,
                    languages TEXT,
                    countries TEXT,
                    awards TEXT,
                    poster TEXT,
                    imdbRating REAL,
                    imdbVotes INTEGER,
                    rottenTomatoes REAL,
                    boxOffice TEXT
                )
            """)
            
            # Extract and process franchise information
            franchise_path = self.genePathExtract(franchiseRecord)
            earliest_year = self.earliestYear(franchiseRecord)
            highest_restriction = self.highestRestriction(franchiseRecord)
            earliest_release = self.earliestRelease(franchiseRecord)
            total_runtime = self.totalRunTime(franchiseRecord)
            directors_club = self.joinChildDirectors(franchiseRecord)
            writers_club = self.joinChildWriters(franchiseRecord)
            fran_cast = self.joinChildCast(franchiseRecord)
            augmented_plot = MetAugment.plotGPT(franchiseRecord)
            babel_tower = self.joinChildLanguages(franchiseRecord)
            fran_continent = self.joinChildCountries(franchiseRecord)
            augmented_awards = MetAugment.awardsGPT(franchiseRecord)
            latest_poster = self.latestPoster(franchiseRecord)
            mean_imdb = self.meanChildIMDBRating(franchiseRecord)
            total_imdb = self.sumChildIMDBVotes(franchiseRecord)
            rotten_mean = self.meanChildRottenTomatoes(franchiseRecord)
            gross_boxoffice = self.sumChildBoxOffice(franchiseRecord)
            
            # Insert franchise record into franchiseassemble table
            cursor.execute("""
                INSERT INTO franchiseassemble (
                    path, folder, title, year, level, class, type, genres, rated, released,
                    runtime, director, writers, cast, plot, languages, countries, awards, poster,
                    imdbRating, imdbVotes, rottenTomatoes, boxOffice
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                franchise_path,
                franchiseRecord['classifications']['folder'],
                franchiseRecord['classifications']['folder'],
                earliest_year,
                franchiseRecord['classifications']['levels'],
                franchiseRecord['classifications']['classes'],
                franchiseRecord['classifications']['type'],
                franchiseRecord['classifications']['genre'],
                highest_restriction,
                earliest_release,
                total_runtime,
                directors_club,
                writers_club,
                fran_cast,
                augmented_plot if augmented_plot else None,
                babel_tower,
                fran_continent,
                augmented_awards if augmented_awards else None,
                latest_poster,
                mean_imdb,
                total_imdb,
                rotten_mean,
                gross_boxoffice
            ))
            conn.commit()

    def genePathExtract(self, franchiseRecord):
        """
        Extracts the franchise path from the filesteps table.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The franchise path.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Find parent folder from filesteps
            cursor.execute("SELECT parent FROM filesteps WHERE child = ?", (franchiseRecord['classifications']['folder'],))
            parent_folder = cursor.fetchone()
            
            if not parent_folder:
                return None
            
            parent_folder = parent_folder[0]
            franchise_path = None
            
            # For each child entry, extract file path from filepaths
            cursor.execute("SELECT filepath FROM filepaths WHERE id IN (SELECT filepath_id FROM filesteps WHERE parent = ?)", (parent_folder,))
            for row in cursor.fetchall():
                file_path = row[0]
                
                # Remove filename to get release_path
                release_path = '/'.join(file_path.split('/')[:-1])
                
                # Remove child from release_path to get franchise_path
                franchise_path = release_path.replace(franchiseRecord['classifications']['folder'], '').strip('/')
                break  # Assuming all child entries have the same franchise path
            
            return franchise_path

    def earliestYear(self, franchiseRecord):
        """
        Finds the earliest year from the filedetails table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The earliest year.
        """
        # ...existing code...

    def highestRestriction(self, franchiseRecord):
        """
        Finds the highest rating restriction for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The highest rating restriction.
        """
        # ...existing code...

    def earliestRelease(self, franchiseRecord):
        """
        Finds the earliest release date from the filemetadata table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The earliest release date.
        """
        # ...existing code...

    def totalRunTime(self, franchiseRecord):
        """
        Sums the total runtime from the filemetadata table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The total runtime.
        """
        # ...existing code...

    def joinChildDirectors(self, franchiseRecord):
        """
        Joins the unique list of directors for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique directors.
        """
        # ...existing code...

    def joinChildWriters(self, franchiseRecord):
        """
        Joins the unique list of writers for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique writers.
        """
        # ...existing code...

    def joinChildCast(self, franchiseRecord):
        """
        Joins the unique list of actors for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique actors.
        """
        # ...existing code...

    def joinChildLanguages(self, franchiseRecord):
        """
        Joins the unique list of languages for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique languages.
        """
        # ...existing code...

    def joinChildCountries(self, franchiseRecord):
        """
        Joins the unique list of countries for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique countries.
        """
        # ...existing code...

    def latestPoster(self, franchiseRecord):
        """
        Finds the most recent movie release within the franchise and returns its poster.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The poster URL of the most recent movie release.
        """
        # ...existing code...

    def meanChildIMDBRating(self, franchiseRecord):
        """
        Calculates the average IMDb rating for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            float: The average IMDb rating.
        """
        # ...existing code...

    def sumChildIMDBVotes(self, franchiseRecord):
        """
        Sums the total IMDb votes for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The total IMDb votes.
        """
        # ...existing code...

    def meanChildRottenTomatoes(self, franchiseRecord):
        """
        Calculates the average Rotten Tomatoes rating for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            float: The average Rotten Tomatoes rating.
        """
        # ...existing code...

    def sumChildBoxOffice(self, franchiseRecord):
        """
        Sums the total box office earnings for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The total box office earnings.
        """
        # ...existing code...