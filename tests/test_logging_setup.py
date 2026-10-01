from app.core.logging_setup import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

logger.debug("This is a debug message (may not show if LOG_LEVEL=INFO)")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")