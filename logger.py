import logging
import os
from config import Config

def setup_logger():
    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(Config.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger('SFSS')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # File Handler
    fh = logging.FileHandler(Config.LOG_FILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

logger = setup_logger()
