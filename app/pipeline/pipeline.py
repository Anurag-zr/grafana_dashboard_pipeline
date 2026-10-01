"""
Pipeline orchestrates the full extract -> raw load -> normalize ->
normalized load -> watermark update sequence for a single source.
"""

from sqlalchemy import text

from app.core.db import Database
from app.core.logging_setup import get_logger
from app.core.models import SourceConfig, SourceType
from app.extract.csv_extractor import CSVExtractor
from app.extract.csv_extractor import FileNotStableError
from app.extract.watermark_store import WatermarkStore
from app.load.raw_loader import RawLoader
from app.load.normalized_loader import NormalizedLoader
from app.normalize.event_normalizer import EventNormalizer
from app.normalize.metric_normalizer import MetricNormalizer

logger = get_logger(__name__)


class Pipeline:

    def __init__(
        self,
        source_config: SourceConfig,
        db: Database,
        extractor: CSVExtractor,
        raw_loader: RawLoader,
        normalized_loader: NormalizedLoader,
        watermark_store: WatermarkStore,
    ):
        self.source_config = source_config
        self.db = db
        self.extractor = extractor
        self.raw_loader = raw_loader
        self.normalized_loader = normalized_loader
        self.watermark_store = watermark_store

        if source_config.source_type == SourceType.EVENT:
            self.normalizer = EventNormalizer()
            self.normalize_target = "events"
        else:
            self.normalizer = MetricNormalizer()
            self.normalize_target = "metrics"

    def run(self) -> None:
        source_name = self.source_config.source_name
        rows_extracted = 0
        rows_loaded = 0
        status = "SUCCESS"
        error_message = None

        try:
            logger.info("Pipeline run started for '%s'", source_name)

            last_watermark = self.watermark_store.get_last_watermark(source_name)
            new_rows = self.extractor.extract(self.source_config, last_watermark)
            rows_extracted = len(new_rows)

            if new_rows.empty:
                logger.info("Pipeline run complete for '%s' (no new rows).", source_name)
            else:
                raw_ids = self.raw_loader.load(new_rows, self.source_config)
                normalized_df = self.normalizer.normalize(new_rows, self.source_config, raw_ids)
                rows_loaded = self.normalized_loader.load(normalized_df, target=self.normalize_target)

                new_watermark = last_watermark + rows_extracted
                self.watermark_store.update_watermark(source_name, new_watermark)

                logger.info(
                    "Pipeline run complete for '%s' | extracted=%d | loaded=%d",
                    source_name, rows_extracted, rows_loaded,
                )

        except FileNotStableError as e:
            status = "SKIPPED"
            error_message = str(e)
            logger.warning("Pipeline run SKIPPED for '%s': %s", source_name, e)

        except Exception as e:
            status = "FAILED"
            error_message = str(e)
            logger.exception("Pipeline run FAILED for '%s': %s", source_name, e)

        self._log_run(source_name, rows_extracted, rows_loaded, status, error_message)
        return status

    def _log_run(self, source_name, rows_extracted, rows_loaded, status, error_message):
        insert_sql = text(
            """
            INSERT INTO pipeline_run_log
                (source_name, rows_extracted, rows_loaded, status, error_message)
            VALUES
                (:source_name, :rows_extracted, :rows_loaded, :status, :error_message)
            """
        )
        with self.db.get_engine().begin() as conn:
            conn.execute(insert_sql, {
                "source_name": source_name,
                "rows_extracted": rows_extracted,
                "rows_loaded": rows_loaded,
                "status": status,
                "error_message": error_message,
            })