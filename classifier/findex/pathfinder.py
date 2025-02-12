import os
from utils import filenaming, save, pathconstruct, titlextract

'''
pathfinder.py is a module that provides a class for finding files in a directory tree.

The PathFinder class is a subclass of the os.path module's DirEntry class. 
It provides a method for finding files in a directory tree that match a specified pattern, in this case extensions. 
The find method takes a directory path and a pattern as arguments, and returns a list 
of file paths that match the pattern and the file name and file title.

The PathFinder class is used by the Findex class in the findex module to find files in a directory tree for indexing.
'''

class PathFinder:
    '''Initialize PathFinder class'''
    def __init__(self, filepath):
        # Initialize file attributes
        self.filepath = filepath # File path
        self.filename = filenaming(filepath) # File name from the filenaming function in the utils module
        self.filetitle = titlextract(filename=self.filename) # File title from the titlextract function in the titlextract module
        self.save = save # Save data to a sqlite3 database

    # Find files in a directory tree
    def find(self, path, extensions):
        '''
        Find files in a directory tree that match a specified pattern.

        The find method takes a directory path and a pattern as arguments, and returns a sqlite3
        table called filepaths of file paths that match the pattern and the file name and file title in the sqlite3 database
        classfier/classified.db.

        :param path: Directory path
        :param extensions: File extensions to match
        :return: List of file paths, file names, and file titles
        '''

        # Initialize file list
        files = []

        for root, dirs, filenames in os.walk(path):
            for filename in filenames:
                # Check if file extension matches pattern
                if filename.endswith(extensions):
                    # Get file path
                    filepath = pathconstruct(root, filename)
                    # Get file name
                    filename = filenaming(filepath)
                    # Get file title
                    filetitle = titlextract(filename)
                    # Add file path, file name, and file title to list
                    files.append((filepath, filename, filetitle))

            for dir in dirs:
                # Check if directory is not empty
                if os.listdir(os.path.join(root, dir)):
                    # Recursively search directory
                    files += self.find(os.path.join(root, dir), extensions)

        # Save to database
        for file in files:
            self.save(columns=['filepath', 'filename', 'filetitle'], values=[file], table_title='filepaths')
        return files