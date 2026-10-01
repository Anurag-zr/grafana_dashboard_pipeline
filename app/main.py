"""
Application entry point: initializes logging, config, DB, and starts
the scheduler to poll all configured sources.
"""

import time

from app.core.logging_setup import configure_logging, get_logger
from app.core.config_loader import ConfigLoader
from app.core.db import Database
from app.pipeline.pipeline_factory import PipelineFactory
from app.scheduler.scheduler import SchedulerService

configure_logging()
logger = get_logger(__name__)


def main():
    settings = ConfigLoader.load_settings()
    db = Database(settings)

    if not db.test_connection():
        logger.error("Database connection failed. Exiting.")
        return

    config_loader = ConfigLoader("./config/sources.yaml")
    sources = config_loader.load_enabled_sources()

    factory = PipelineFactory(db)
    scheduler = SchedulerService(factory, retry_delay_seconds=30)

    logger.info("Running all sources once at startup...")
    for source in sources:
        scheduler.run_once(source)

    scheduler.schedule_all(sources)
    scheduler.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
        scheduler.shutdown()


if __name__ == "__main__":
    main()