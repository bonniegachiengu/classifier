import sqlite3
from datetime import datetime
from classifier.utils.config import DB_PATH, RATING_ORDER
from classifier.utils.logger import log_info, log_error, log_debug, log_warning
from .augmentor import MetAugment

class MetAssembly:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH)
        self.cursor = self.db.cursor()

    def fetchType(self):
        """
        Fetches and processes types from the classifications table.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Process franchises from classifications
            cursor.execute("SELECT * FROM classifications WHERE type = 'Franchise'")
            for record in cursor.fetchall():
                # Convert record to dictionary
                record_dict = {
                    'file_id': record[0],
                    'classifications': {
                        'folder': record[1],
                        'levels': record[2],
                        'classes': record[3],
                        'type': record[4],
                        'genre': record[5]
                    }
                }
                self.assembleFranchises(record_dict)

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
                    id INTEGER PRIMARY KEY,
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
                    boxOffice TEXT,
                    file_id INTEGER,
                    FOREIGN KEY (file_id) REFERENCES classifications (file_id) ON DELETE CASCADE
                )
            """)
            
            # Check if the franchise already exists in the table
            cursor.execute("""
                SELECT id FROM franchiseassemble WHERE folder = ? AND file_id = ?
            """, (franchiseRecord['classifications']['folder'], franchiseRecord['file_id']))
            if cursor.fetchone():
                log_info("Franchise {} already exists in the table. Skipping...".format(franchiseRecord['classifications']['folder']))
                return
            
            # Extract and process franchise information
            franchise_path = self.genePathExtract(franchiseRecord)
            if franchise_path is None:
                log_error("Failed to extract path for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return
            
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
            
            # Insert or update franchise record in franchiseassemble table
            cursor.execute("""
                INSERT OR REPLACE INTO franchiseassemble (
                    path, folder, title, year, level, class, type, genres, rated, released,
                    runtime, director, writers, cast, plot, languages, countries, awards, poster,
                    imdbRating, imdbVotes, rottenTomatoes, boxOffice, file_id
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
                gross_boxoffice,
                franchiseRecord['file_id']
            ))
            conn.commit()

    def genePathExtract(self, franchiseRecord):
        """
        Extracts the franchise path from the filepaths table.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The franchise path.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Fetch the file path using file_id from classifications
            cursor.execute("SELECT filepath FROM filepaths WHERE id = ?", (franchiseRecord['file_id'],))
            row = cursor.fetchone()
            if row:
                file_path = row[0]
                # Split the path and remove the last two parts (filename and file folder)
                path_parts = file_path.split("\\")
                franchise_path = "\\".join(path_parts[:-2])
            else:
                franchise_path = None
            
            if franchise_path is None:
                log_warning("Franchise path could not be determined for franchise: {}".format(franchiseRecord['classifications']['folder']))
            
            log_info("Franchise path for franchise {}: {}".format(franchiseRecord['classifications']['folder'], franchise_path))
            return franchise_path

    def earliestYear(self, franchiseRecord):
        """
        Finds the earliest year from the filedetails table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The earliest year.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filedetails.year
                FROM filedetails
                JOIN filepaths ON filedetails.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            years = [row[0] for row in cursor.fetchall()]

            if not years:
                log_info("No years found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return None
            
            # Return the earliest year
            return min(years)

    def highestRestriction(self, franchiseRecord):
        """
        Finds the highest rating restriction for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The highest rating restriction.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filemetadata
            cursor.execute("""
                SELECT filemetadata.rated
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            ratings = [row[0] for row in cursor.fetchall()]

            if not ratings:
                log_info("No ratings found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return None
            
            # Find the highest rating based on the specified order
            highest_rating = max(ratings, key=lambda r: RATING_ORDER.index(r) if r in RATING_ORDER else -1)

            log_info("Highest rating for franchise {}: {}".format(franchiseRecord['classifications']['folder'], highest_rating))
            return highest_rating

    def earliestRelease(self, franchiseRecord):
        """
        Finds the earliest release date from the filemetadata table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The earliest release date.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.released
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ? 
            """, (franchiseRecord['classifications']['folder'],))

            release_dates = [row[0] for row in cursor.fetchall()]

            if not release_dates:
                log_info("No release dates found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return None
            
            # Convert release dates to datetime objects and find the earliest date
            release_dates = [datetime.strptime(date, "%d %b %Y") for date in release_dates]
            earliest_release = min(release_dates).strftime("%d %b %Y")

            log_info("Earliest release for franchise {} are: {}".format(franchiseRecord['classifications']['folder'], earliest_release))
            return earliest_release

    def totalRunTime(self, franchiseRecord):
        """
        Sums the total runtime from the filemetadata table for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The total runtime.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.runtime
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps on filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            runtimes = [int(row[0].split()[0]) for row in cursor.fetchall() if row[0]]

            if not runtimes:
                log_info("No runtimes found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return 0
            
            # Sum all runtimes
            total_runtime = sum(runtimes)

            log_info("Total runtime for franchise {}: {}".format(franchiseRecord['classifications']['folder'], total_runtime))
            return total_runtime

    def joinChildDirectors(self, franchiseRecord):
        """
        Joins the unique list of directors for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique directors.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.director
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            directors = set()
            for row in cursor.fetchall():
                director_list = row[0].split(', ')
                directors.update(director_list)

            if not directors:
                log_info("No directors found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Join unique directors into a comma-separated list
            unique_directors = ", ".join(directors)

            log_info("Directors for franchise {}: {}".format(franchiseRecord['classifications']['folder'], unique_directors))
            return unique_directors

    def joinChildWriters(self, franchiseRecord):
        """
        Joins the unique list of writers for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique writers.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.writer
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            writers = set()
            for row in cursor.fetchall():
                writer_list = row[0].split(', ')
                writers.update(writer_list)

            if not writers:
                log_info("No writers found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Join unique writers into a comma-separated list
            unique_writers = ", ".join(writers)

            log_info("Writers for franchise {}: {}".format(franchiseRecord['classifications']['folder'], unique_writers))
            return unique_writers

    def joinChildCast(self, franchiseRecord):
        """
        Joins the unique list of actors for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique actors.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.actors
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            actors = set()
            for row in cursor.fetchall():
                actor_list = row[0].split(', ')
                actors.update(actor_list)

            if not actors:
                log_info("No actors found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Join unique actors into a comma-separated list
            unique_actors = ", ".join(actors)

            log_info("Actors for franchise {}: {}".format(franchiseRecord['classifications']['folder'], unique_actors))
            return unique_actors

    def joinChildLanguages(self, franchiseRecord):
        """
        Joins the unique list of languages for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique languages.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.language
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            languages = set()
            for row in cursor.fetchall():
                language_list = row[0].split(', ')
                languages.update(language_list)

            if not languages:
                log_info("No languages found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Join unique languages into a comma-separated list
            unique_languages = ", ".join(languages)

            log_info("Languages for franchise {}: {}".format(franchiseRecord['classifications']['folder'], unique_languages))
            return unique_languages

    def joinChildCountries(self, franchiseRecord):
        """
        Joins the unique list of countries for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: A comma-separated list of unique countries.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.country
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            countries = set()
            for row in cursor.fetchall():
                country_list = row[0].split(', ')
                countries.update(country_list)

            if not countries:
                log_info("No countries found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Join unique countries into a comma-separated list
            unique_countries = ", ".join(countries)

            log_info("Countries for franchise {}: {}".format(franchiseRecord['classifications']['folder'], unique_countries))
            return unique_countries

    def latestPoster(self, franchiseRecord):
        """
        Finds the most recent movie release within the franchise and returns its poster.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            str: The poster URL of the most recent movie release.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find the most recent movie linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.poster, filemetadata.released
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            posters = [(row[0], datetime.strptime(row[1], "%d %b %Y")) for row in cursor.fetchall() if row[1]]

            if not posters:
                log_info("No poster found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return ""
            
            # Find the poster of the most recent release
            latest_poster = max(posters, key=lambda x: x[1])[0]

            log_info("Latest poster for franchise {}: {}".format(franchiseRecord['classifications']['folder'], latest_poster))
            return latest_poster

    def meanChildIMDBRating(self, franchiseRecord):
        """
        Calculates the average IMDb rating for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            float: The average IMDb rating.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filemetadata
            cursor.execute("""
                SELECT filemetadata.imdbRating
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            imdb_ratings = [row[0] for row in cursor.fetchall() if row[0] not in ('N/A', None)]

            if not imdb_ratings:
                log_info("No IMDb ratings found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return 0.0

            # Convert ratings to float
            imdb_ratings = [float(rating.split('/')[0]) for rating in imdb_ratings]

            # Calculate the average IMDb rating
            mean_imdb_rating = sum(imdb_ratings) / len(imdb_ratings)
            log_info("Mean IMDb rating for franchise {}: {}".format(franchiseRecord['classifications']['folder'], mean_imdb_rating))
            return mean_imdb_rating

    def sumChildIMDBVotes(self, franchiseRecord):
        """
        Sums the total IMDb votes for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The total IMDb votes.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.imdbVotes
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            imdb_votes = [row[0] for row in cursor.fetchall() if row[0] not in ('N/A', None)]

            if not imdb_votes:
                log_info("No IMDb votes found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return 0

            # Convert votes to int
            imdb_votes = [int(vote.replace(',', '')) for vote in imdb_votes]

            # Return the total IMDb votes
            total_imdb_votes = sum(imdb_votes)
            log_info("Total IMDb votes for franchise {}: {}".format(franchiseRecord['classifications']['folder'], total_imdb_votes))
            return total_imdb_votes

    def meanChildRottenTomatoes(self, franchiseRecord):
        """
        Calculates the average Rotten Tomatoes rating for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            float: The average Rotten Tomatoes rating.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.rottenTomatoes
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            rotten_ratings = [row[0] for row in cursor.fetchall() if row[0] not in ('N/A', None)]

            if not rotten_ratings:
                log_info("No Rotten Tomatoes ratings found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return 0.0

            # Convert ratings to float
            rotten_ratings = [float(rating.replace('%', '')) for rating in rotten_ratings]

            # Return the average Rotten Tomatoes rating
            average_rotten_rating = sum(rotten_ratings) / len(rotten_ratings)
            log_info("Average Rotten Tomatoes rating for franchise {}: {}".format(franchiseRecord['classifications']['folder'], average_rotten_rating))
            return average_rotten_rating

    def sumChildBoxOffice(self, franchiseRecord):
        """
        Sums the total box office earnings for the given franchise.

        Args:
            franchiseRecord (dict): A dictionary containing franchise metadata.

        Returns:
            int: The total box office earnings.
        """
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Find all movies linked to franchiseRecord in filesteps
            cursor.execute("""
                SELECT filemetadata.boxOffice
                FROM filemetadata
                JOIN filepaths ON filemetadata.file_id = filepaths.id
                JOIN filesteps ON filepaths.id = filesteps.filepath_id
                WHERE filesteps.parent = ?
            """, (franchiseRecord['classifications']['folder'],))

            earnings = [row[0] for row in cursor.fetchall() if row[0] not in ('N/A', None)]

            if not earnings:
                log_info("No box office earnings found for franchise: {}".format(franchiseRecord['classifications']['folder']))
                return 0

            # Convert earnings to int
            earnings = [int(earning.replace('$', '').replace(',', '')) for earning in earnings]

            # Return the total box office earnings
            total_earnings = sum(earnings)
            log_info("Total box office earnings for franchise {}: {}".format(franchiseRecord['classifications']['folder'], total_earnings))
            return total_earnings