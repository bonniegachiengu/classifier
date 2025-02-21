import logging
from .config import DEBUG_MODE

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log_info(message, *args):
    logging.info(message, *args)

def log_debug(message, *args):
    logging.debug(message, *args)

def log_warning(message, *args):
    logging.warning(message, *args)

def log_error(message, *args):
    logging.error(message, *args)
