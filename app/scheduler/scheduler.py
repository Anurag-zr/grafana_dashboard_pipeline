"""
Schedules periodic pipeline runs per source, based on each source's
configured poll_interval. Handles short-interval retries when a run
is SKIPPED (e.g. due to a locked/unstable CSV file).
"""

import re
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logging_setup import get_logger
from app.core.models import SourceConfig
from app.pipeline.pipeline_factory import PipelineFactory

logger = get_logger(__name__)

_INTERVAL_PATTERN = re.compile(r"^(\d+)([smhd])$")
_UNIT_TO_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


class SchedulerService:

    def __init__(self, pipeline_factory: PipelineFactory, retry_delay_seconds: int = 60):
        self.pipeline_factory = pipeline_factory
        self.retry_delay_seconds = retry_delay_seconds
        self.scheduler = BackgroundScheduler()

    @staticmethod
    def parse_interval_to_seconds(interval_str: str) -> int:
        match = _INTERVAL_PATTERN.match(interval_str)
        if not match:
            raise ValueError(f"Invalid interval format: '{interval_str}'")
        value, unit = match.groups()
        return int(value) * _UNIT_TO_SECONDS[unit]

    def _run_source(self, source_config: SourceConfig) -> None:
        logger.info("Scheduled poll triggered for '%s'", source_config.source_name)
        pipeline = self.pipeline_factory.build(source_config)
        status = pipeline.run()

        if status == "SKIPPED":
            retry_time = datetime.now() + timedelta(seconds=self.retry_delay_seconds)
            logger.warning(
                "'%s' was SKIPPED (likely locked/unstable file). Retry scheduled at %s.",
                source_config.source_name, retry_time.strftime("%H:%M:%S"),
            )
            self.scheduler.add_job(
                func=self._run_source,
                args=[source_config],
                trigger="date",
                run_date=retry_time,
                id=f"{source_config.source_name}_retry",
                replace_existing=True,
            )

    def schedule_all(self, sources: list[SourceConfig]) -> None:
        for source_config in sources:
            interval_seconds = self.parse_interval_to_seconds(source_config.poll_interval)
            self.scheduler.add_job(
                func=self._run_source,
                args=[source_config],
                trigger="interval",
                seconds=interval_seconds,
                id=source_config.source_name,
                replace_existing=True,
            )
            logger.info(
                "Scheduled '%s' every %ds (%s)",
                source_config.source_name, interval_seconds, source_config.poll_interval,
            )

    def run_once(self, source_config: SourceConfig) -> None:
        logger.info("Manual run triggered for '%s'", source_config.source_name)
        self._run_source(source_config)

    def start(self) -> None:
        self.scheduler.start()
        logger.info("Scheduler started.")

    def shutdown(self) -> None:
        self.scheduler.shutdown()
        logger.info("Scheduler shutdown.")