"""Logging configuration for the application."""

import logging
from logging.handlers import RotatingFileHandler

from config.settings import settings


def setup_logger(name: str = "doc2md") -> logging.Logger:
    """Set up and return a logger instance that logs to console and rotating file.

    Does not log sensitive document content.
    """
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating File Handler (Max 5MB, keep 3 backups)
    log_file = settings.LOGS_DIR / "app.log"
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as err:
        # Fallback if log file cannot be opened
        logger.warning(f"Could not initialize file logger: {err}")

    logger.propagate = False
    return logger


logger = setup_logger()

