import logging
import sys
from pathlib import Path

from config import APP_NAME, LOG_FILE, LOG_LEVEL


class AppLogger:
    def __init__(self, name: str = APP_NAME, log_file: str = LOG_FILE):
        self.logger = logging.getLogger(name)
        level = LOG_LEVEL
        self.logger.setLevel(level)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d - %(message)s"
            )

            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            log_path = Path(log_file)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger


logger = AppLogger().get_logger()
