"""
This is the classifier package for media management applications.
It includes modules for metadata collection, file indexing, and content analysis.
"""

from .db.crawler import Crawler
from .finder import Findex
from .generator import Generator