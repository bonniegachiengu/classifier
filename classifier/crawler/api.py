from utils import fetch
import requests


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
                return data # Return movie details
            else:
                print(f"Movie not found: {title} ({year})")
        else:
            print(f"Error: {response.status_code} Failed to fetch data for {title} ({year})")

        return None # Return None if failed to fetch data
    
# Example usage
if __name__ == '__main__':
    api = API("http://www.omdbapi.com/", "1787320b")

    # Collect title and year from database
    movies = api.collect()

    # Search OMDb API for movie details
    for title, year in movies:
        data = api.search(title, year)
        if data:
            print(data)