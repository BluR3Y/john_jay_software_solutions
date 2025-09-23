# wbm/logging_config.py
import logging
from pathlib import Path
from logging import _nameToLevel

class ProgramLogger:
    def __init__(self, name: str = "Script"):
        self.logger = logging.getLogger(name)

    def config_logger(self, save_path: str, min_level: str = "DEBUG", log_name: str = "Script.log"):
        log_path = Path(save_path)
        log_path.mkdir(parents=True, exist_ok=True)

        level = _nameToLevel.get(min_level.upper())
        if level is None:
            raise ValueError(f"Invalid log level: {min_level}")
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            file_handler = logging.FileHandler(log_path / log_name)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def get_logger(self) -> logging.Logger:
        return self.logger

# Singleton instance
logger = ProgramLogger()
