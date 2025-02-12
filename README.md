# Classifier Package

`Classifier` is a package that can be imported into other projects and used to scan a folder, extract metadata on specified type of files using `Classifier` packages that utilize APIs to external databases, GPT4All, or internal algorithms. This include `crawler`, `generator`, and `findex` respectively.

## Project Structure

```plaintext
classifier
├── findex
│   ├── __init__.py
│   ├── findex.py
│   ├── pathfinder.py
│   ├── stepextractor.py
│   ├── detailsextractor.py
│   └── utils.py
├── crawler
│   ├── __init__.py
│   └── crawler.py
├── generator
│   ├── __init__.py
│   └── generator.py
├── requirements.txt
└── README.md
```

## Findex Package

The `findex` package is responsible for finding and extracting metadata from files in a directory tree. It includes the following modules:

- `findex.py`: Main module for the `findex` package.
- `pathfinder.py`: Provides the `PathFinder` class for finding files in a directory tree.
- `stepextractor.py`: Provides the `StepExtractor` class for extracting directory steps from file paths.
- `detailsextractor.py`: (To be implemented) Provides functions for extracting detailed metadata from files.
- `utils.py`: Provides utility functions for file and path operations, and database interactions.

## Usage

To use the `findex` package, you can initialize the `PathFinder` and `StepExtractor` classes to find files and extract directory steps, respectively.

Example usage:

```python
from findex.pathfinder import PathFinder
from findex.stepextractor import StepExtractor

# Initialize PathFinder object
pathfinder = PathFinder(filepath='path/to/directory')

# Find files in directory tree
pathfinder.find(path='path/to/directory', extensions=('.txt', '.pdf'))

# Initialize StepExtractor object
stepextractor = StepExtractor()

# Extract directory steps from file paths
stepextractor.extract()
```
