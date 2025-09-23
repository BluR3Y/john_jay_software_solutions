import logging

from pathlib import Path
from logging import _nameToLevel

class ProgramLogger:

    def __init__(self):
        # Create a logger
        self.logger = logging.getLogger(__name__)
    
    # Levels: debug, info, warning, error, critical
    def config_logger(self, save_path: str, min_level: str = "debug"):
        log_path = Path(save_path)
        log_path.mkdir(parents=True, exist_ok=True)

        level = logging.getLevelName(min_level.upper())
        if not isinstance(level, int):
            raise ValueError(f"Invalid log level: {min_level}")
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # File handler
            file_handler = logging.FileHandler(log_path / f"migration_script.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Stream handler (console)
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def get_logger(self):
        return self.logger

logger = ProgramLogger()