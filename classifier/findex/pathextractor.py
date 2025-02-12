import os
from utils import filenamer

# Define pathextractor function to extract the path of a file from its root and filename
def pathextractor(root, filename):
    """
    Extract the path of a file from its root and filename, or dir.
    
    The pathextractor function takes the root directory and filename of a file as arguments, 
    and returns the full path of the file.
    
    :param root: Root directory
    :param filename: Filename
    :return: Full path of the file
    """
    
    # get filename from filenamer function in utils module
    filename = filenamer(filename)

    # Return full path
    return os.path.join(root, filename)