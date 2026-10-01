"""
Loads normalized dataframes into normalized_events / normalized_metrics,
using upsert (ON CONFLICT DO NOTHING) as a safeguard against duplicate
inserts caused by partial/failed pipeline runs.
"""

import pandas as pd
from sqlalchemy import text

from app.core.db import Database
from app.core.logging_setup import get_logger
from app.load.base_loader import AbstractLoader

logger = get_logger(__name__)


class NormalizedLoader(AbstractLoader):

    def __init__(self, db: Database):
        self.db = db

    def load(self, df: pd.DataFrame, target: str) -> int:
        if target == "events":
            return self._load_events(df)
        elif target == "metrics":
            return self._load_metrics(df)
        else:
            raise ValueError(f"Unknown target '{target}'. Expected 'events' or 'metrics'.")

    def _load_events(self, df: pd.DataFrame) -> int:
        if df.empty:
            logger.info("No event rows to load.")
            return 0

        insert_sql = text(
            """
            INSERT INTO normalized_events
                (source_system, source_event_id, event_time, status, category,
                 severity, owner, description, details, raw_table_name, raw_id)
            VALUES
                (:source_system, :source_event_id, :event_time, :status, :category,
                 :severity, :owner, :description, CAST(:details AS JSONB),
                 :raw_table_name, :raw_id)
            ON CONFLICT (source_system, source_event_id) DO NOTHING
            """
        )

        inserted_count = 0
        with self.db.get_engine().begin() as conn:
            for _, row in df.iterrows():
                result = conn.execute(insert_sql, row.to_dict())
                inserted_count += result.rowcount

        skipped_count = len(df) - inserted_count
        logger.info(
            "Loaded %d new event row(s), skipped %d existing (ON CONFLICT).",
            inserted_count, skipped_count,
        )
        return inserted_count

    def _load_metrics(self, df: pd.DataFrame) -> int:
        if df.empty:
            logger.info("No metric rows to load.")
            return 0

        insert_sql = text(
            """
            INSERT INTO normalized_metrics
                (source_system, metric_name, metric_value, metric_rank,
                 period_start, period_end, source_row_key, raw_table_name, raw_id)
            VALUES
                (:source_system, :metric_name, :metric_value, :metric_rank,
                 :period_start, :period_end, :source_row_key, :raw_table_name, :raw_id)
            ON CONFLICT (source_system, metric_name, period_end, metric_rank) DO NOTHING
            """
        )

        inserted_count = 0
        with self.db.get_engine().begin() as conn:
            for _, row in df.iterrows():
                result = conn.execute(insert_sql, row.to_dict())
                inserted_count += result.rowcount

        skipped_count = len(df) - inserted_count
        logger.info(
            "Loaded %d new metric row(s), skipped %d existing (ON CONFLICT).",
            inserted_count, skipped_count,
        )
        return inserted_count