import requests
import sqlite3
from utils import fetch

'''
API is a class used to get the data from the web using API. For instance from OMDb API for now.

API will take the movie title and year from filedetails table in my classified.db database,
search the OMDb API for the movie details such as cast, director, genre, plot, rating, and 
most importantly the poster URL and in the filemetadata table in the classified.db database.

API will have a collect title and year method from findex.utils.fetch to collect the movie title and year from the
filedetails table in the classified.db database.

API will have a search method to search the OMDb API for the movie details such as cast, 
director, genre, plot, rating, and most importantly the poster URL.

API will have a save method to save the movie details such as cast, director, genre, plot, 
rating, and poster URL in the filemetadata table in the classified.db database.
'''

class API:
    '''Initialize API class'''
    def __init__(self, url, apikey, dbpath='../classified.db'):
        self.url = url
        self.apikey = apikey
        self.dbpath = dbpath

    def collect(self):
        '''Collect title and year from filedetails table in classified.db'''

        # Fetch data from database
        columns = ['title', 'year']
        table_title = 'filedetails'
        data = fetch(columns, table_title)

        return data
    
    def search(self, title, year):
        '''Search OMDb API for the movie details'''
        
        # Define parameters
        params = {
            "t": title,
            "y": year,
            "apikey": self.apikey
        }
        response = requests.get(self.url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == 'True':
                self.save(data) # Save data to database
                print(f"Successfully saved movie details for {title} ({year})") # Print success message
                return data # Return movie details
            else:
                # Print error message
                print(f"Movie details not found for {title} ({year})")
        else:
            # Print error message
            print(f"Error: {response.status_code}: Failed to fetch movie details for {title} ({year})")
        
        return None


    def save(self, data):
        '''Save the retrieved movie metadata to the filemetadata table in classified.db'''

        conn = sqlite3.connect(self.dbpath)
        cursor = conn.cursor()

        # Create filemetadata table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filemetadata (
                imdbID TEXT PRIMARY KEY,
                title TEXT,
                year TEXT,
                rated TEXT,
                released TEXT,
                runtime TEXT,
                genre TEXT,
                director TEXT,
                writer TEXT,
                actors TEXT,
                plot TEXT,
                language TEXT,
                country TEXT,
                awards TEXT,
                poster TEXT,
                metascore TEXT,
                imdbRating TEXT,
                imdbVotes TEXT,
                type TEXT,
                boxoffice TEXT
            )
        """)

        # Create filemetadata table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filemetadata (
                imdbID TEXT PRIMARY KEY,
                title TEXT,
                year TEXT,
                rated TEXT,
                released TEXT,
                runtime TEXT,
                genre TEXT,
                director TEXT,
                writer TEXT,
                actors TEXT,
                plot TEXT,
                language TEXT,
                country TEXT,
                awards TEXT,
                poster TEXT,
                metascore TEXT,
                imdbRating TEXT,
                imdbVotes TEXT,
                type TEXT,
                boxoffice TEXT
            )
        """)

        # Insert or update the metadata
        cursor.execute("""
            INSERT INTO filemetadata (
                imdbID, title, year, rated, released, runtime, genre, director, 
                writer, actors, plot, language, country, awards, poster, 
                metascore, imdbRating, imdbVotes, type, boxoffice
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(imdbID) DO UPDATE SET
                title = excluded.title,
                year = excluded.year,
                rated = excluded.rated,
                released = excluded.released,
                runtime = excluded.runtime,
                genre = excluded.genre,
                director = excluded.director,
                writer = excluded.writer,
                actors = excluded.actors,
                plot = excluded.plot,
                language = excluded.language,
                country = excluded.country,
                awards = excluded.awards,
                poster = excluded.poster,
                metascore = excluded.metascore,
                imdbRating = excluded.imdbRating,
                imdbVotes = excluded.imdbVotes,
                type = excluded.type,
                boxoffice = excluded.boxoffice
        """, (
            data.get("imdbID"),
            data.get("Title"),
            data.get("Year"),
            data.get("Rated"),
            data.get("Released"),
            data.get("Runtime"),
            data.get("Genre"),
            data.get("Director"),
            data.get("Writer"),
            data.get("Actors"),
            data.get("Plot"),
            data.get("Language"),
            data.get("Country"),
            data.get("Awards"),
            data.get("Poster"),
            data.get("Metascore"),
            data.get("imdbRating"),
            data.get("imdbVotes"),
            data.get("Type"),
            data.get("BoxOffice")
        ))

        conn.commit()
        conn.close()

# Example usage
if __name__ == '__main__':
    api = API("http://www.omdbapi.com/", "1787320b")

    # Collect title and year from database
    movies = api.collect()

    # Search OMDb API for movie details
    for title, year in movies:
        movie_details = api.search(title, year)
        if movie_details:
            print(movie_details)
            break
    else:

        print("No movie details found")

# Output
# Successfully saved movie details for The Shawshank Redemption (1994)

            