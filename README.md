# Classifier Package

Classifier is a Python package designed for media management applications. It provides tools for collecting metadata, indexing files, and analyzing content to enhance media management workflows.

## Modules

### Crawler

The `crawler` module connects to external databases (e.g., TMDb) to fetch movie details, posters, and additional metadata. It supports multiple sources for cross-verification.

### Findex

The `findex` module scans specified directories for media files (e.g., .mp4, .avi) and stores file paths and basic information in a structured database.

### Generator

The `generator` module utilizes GPT4All to generate summaries and themes for media files. It enhances metadata by adding descriptions, keywords, and possible genres.

## Installation

To install the Classifier package, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd classifier
pip install -r requirements.txt
```

## Usage

After installation, you can use the modules as follows:

```python
from classifier.crawler import Crawler
from classifier.findex import Findex
from classifier.generator import Generator

# Example usage
crawler = Crawler()
findex = Findex()
generator = Generator()
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
