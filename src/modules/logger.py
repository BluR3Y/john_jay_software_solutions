import logging
from pathlib import Path

def config_logger(save_path):
    # Create a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set the minimum level for this logger

    # Create a file handler and set its format
    file_handler = logging.FileHandler(Path(save_path) / 'migration_script_logs.log')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a stream handler (for console output) and set its format
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)