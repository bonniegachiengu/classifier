import logging

# Configure logging to log to a file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("c:/Users/DELL/OneDrive/Documents/Projects/Packages/Classifier/classifier/classified.log"),
        logging.StreamHandler()
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)

def log_info(message, *args):
    logger.info(message, *args)

def log_debug(message, *args):
    logger.debug(message, *args)

def log_warning(message, *args):
    logger.warning(message, *args)

def log_error(message, *args):
    logger.error(message, *args)
