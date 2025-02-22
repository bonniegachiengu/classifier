import os


# Database file path (can be updated later if needed)
DB_PATH = os.path.join(os.getcwd(), "../classified.db")

# Filesteps exclusions (used in Ancestry algorithm)
EXCLUDED_FOLDERS = {"E:", "Films", "Media", "Series", "Movies"}

# Logging settings (can be toggled)
DEBUG_MODE = True

# Metadata merging fields (used in MetAssembly)
METADATA_FIELDS = [
    "title", "year", "genre", "type", "runtime",
    "language", "country", "imdbID", "imdbRating"
]

