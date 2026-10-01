"""
Tracks per-source ingestion progress (row-count watermark) in the
pipeline_watermarks table, so the extractor knows where it left off.
"""

from sqlalchemy import text

from app.core.db import Database
from app.core.logging_setup import get_logger

logger = get_logger(__name__)


class WatermarkStore:
    """
    Reads and writes the 'last row count read' watermark per source.

    NOTE (known limitation): this assumes CSVs are strictly append-only.
    See KNOWN_LIMITATIONS.md for details and future mitigation plan.
    """

    def __init__(self, db: Database):
        self.db = db

    def get_last_watermark(self, source_name: str) -> int:
        """
        Returns the last recorded row count for this source.
        Returns 0 if the source has never been processed before.
        """
        query = text(
            "SELECT last_value FROM pipeline_watermarks WHERE source_name = :source_name"
        )
        with self.db.get_engine().connect() as conn:
            result = conn.execute(query, {"source_name": source_name}).fetchone()

        if result is None:
            logger.info("No watermark found for '%s'; starting from 0.", source_name)
            return 0

        last_value = int(result[0]) if result[0] is not None else 0
        logger.debug("Watermark for '%s' = %d", source_name, last_value)
        return last_value

    def update_watermark(self, source_name: str, value: int) -> None:
        """
        Inserts or updates the watermark for this source (upsert).
        """
        query = text(
            """
            INSERT INTO pipeline_watermarks (source_name, last_value, last_run_at)
            VALUES (:source_name, :value, NOW())
            ON CONFLICT (source_name)
            DO UPDATE SET last_value = :value, last_run_at = NOW()
            """
        )
        with self.db.get_engine().begin() as conn:
            conn.execute(query, {"source_name": source_name, "value": str(value)})

        logger.info("Watermark updated for '%s' -> %d", source_name, value)

