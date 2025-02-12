from utils import filenamer

def titlextractor(filename):
    '''
    titlextractor.py is a module that provides a function for extracting the title of a file from its name.

    The titlextractor function takes a file name as an argument and returns the title of the file. 
    The title is extracted by changing filenames with this format "Duck.Duck.Goose.2018.720p.BluRay.x264-[YTS.AM].mp4" to
    "Duck Duck Goose".

    The titlextractor function is used by the PathFinder class in the pathfinder module to extract the title of a file from its name.
    '''

    # Remove file extension
    filename = filenamer(filename)
    filename = filename.split('.')[0:-1] # Remove file extension

    # Extract title up to year
    title = [] # Initialize title list
    for word in filename:
        if word.isnumeric() and len(word) == 4:
            break
        title.append(word)

    # Join title words
    title = ' '.join(title)

    return title

# # Test titlextractor function
# filename = "Duck.Duck.Goose.2018.720p.BluRay.x264-[YTS.AM].mp4"
# print(titlextractor(filename)) # Output: Duck Duck Goose
# filename = "The.Lion.King.2019.720p.BluRay.x264-[YTS.AM].avi"
# print(titlextractor(filename)) # Output: The Lion King

# # Run the test with the following command:
# # python titlextractor.py




