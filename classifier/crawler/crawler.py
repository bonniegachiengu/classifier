

'''
Crawler class is used to crawl the web and get the data from the web.
It uses API and web scraping to get the data from the web.

The Crawler class is composed of the API and WebScraper classes.

The API class is used to get the data from the web using API. For instance from 
OMDb API for now.

The WebScraper class is used to get the data from the web using web scraping.
For instance metadata from Wikipedia for now.

The Crawler class provides a method for getting the data from the web using API and web scraping.
'''

# class Crawler:
#     '''Initialize Crawler class'''
#     def __init__(self, url, apikey):
#         self.url = url
#         self.apikey = apikey

#     def run(self):
#         '''Run the Crawler process'''

#         # Get data from the web using API: API
#         api = API(url=self.url, apikey=self.apikey)