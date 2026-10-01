"""
Centralized logging configuration for the CSV ingestion pipeline.

This module is intentionally standalone (no dependency on config_loader)
so it can be initialized as the very first step of the application,
before any other module (extract/normalize/load/pipeline) is imported.
"""

import logging
import os
import sys
from logging import Logger

from dotenv import load_dotenv

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(log_level: str = None, log_path: str = None) -> None:
    """
    Configure the root logger for the entire application.

    Should be called exactly once, as early as possible (e.g. in main.py),
    before any module-level loggers are used.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR, CRITICAL.
                   Falls back to LOG_LEVEL env var, then INFO.
        log_path: File path where logs should be written.
                  Falls back to LOG_PATH env var, then ./logs/pipeline.log
    """
    global _configured
    if _configured:
        logging.getLogger(__name__).debug(
            "configure_logging() called again; ignoring (already configured)."
        )
        return

    load_dotenv()  # loads .env into os.environ if present; no-op otherwise

    resolved_level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    resolved_path = log_path or os.getenv("LOG_PATH", "./logs/pipeline.log")

    log_dir = os.path.dirname(resolved_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    numeric_level = getattr(logging, resolved_level, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # avoid duplicate handlers on re-import

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(resolved_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True

    logging.getLogger(__name__).info(
        "Logging configured | level=%s | file=%s", resolved_level, resolved_path
    )


def get_logger(name: str) -> Logger:
    """
    Retrieve a named logger for a specific module/class.

    Usage:
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)