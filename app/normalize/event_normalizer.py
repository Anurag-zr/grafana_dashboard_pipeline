"""
Normalizes Type A (event-level) raw data into the common normalized_events shape.
"""

import json

import pandas as pd

from app.core.logging_setup import get_logger
from app.core.models import SourceConfig
from app.normalize.base_normalizer import AbstractNormalizer

logger = get_logger(__name__)

SPINE_FIELDS = ["status", "category", "severity", "owner", "description"]


class EventNormalizer(AbstractNormalizer):

    def normalize(self, df: pd.DataFrame, source_config: SourceConfig, raw_ids: list[int]) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=[
                "source_system", "source_event_id", "event_time", "status",
                "category", "severity", "owner", "description", "details",
                "raw_table_name", "raw_id",
            ])

        working = df.copy()

        # Reverse config mapping: {our_field: csv_col} -> {csv_col: our_field}
        mapping = source_config.column_mapping or {}
        reversed_mapping = {csv_col: our_field for our_field, csv_col in mapping.items()}

        id_col = source_config.id_column
        date_col = source_config.date_column

        mapped_csv_columns = set(reversed_mapping.keys()) | {id_col, date_col}
        unmapped_columns = [c for c in working.columns if c not in mapped_csv_columns]

        records = []
        for idx, row in working.iterrows():
            record = {
                "source_system": source_config.source_system,
                "source_event_id": row[id_col],
                "event_time": pd.to_datetime(row[date_col], errors="coerce").date()
                    if pd.notna(row[date_col]) else None,
            }

            for spine_field in SPINE_FIELDS:
                csv_col = mapping.get(spine_field)
                record[spine_field] = row[csv_col] if csv_col and csv_col in working.columns else None

            details = {col: row[col] for col in unmapped_columns if pd.notna(row[col])}
            record["details"] = json.dumps(details)

            record["raw_table_name"] = f"raw_{source_config.source_name.lower()}"
            record["raw_id"] = raw_ids[idx]

            records.append(record)

        result_df = pd.DataFrame(records)

        null_event_time_count = result_df["event_time"].isna().sum()
        if null_event_time_count > 0:
            logger.warning(
                "%d row(s) in '%s' had unparseable event_time values.",
                null_event_time_count, source_config.source_name,
            )

        logger.info(
            "Normalized %d event row(s) for '%s'",
            len(result_df), source_config.source_name,
        )
        return result_df