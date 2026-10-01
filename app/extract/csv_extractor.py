"""
Reads pilot CSV files and extracts only rows beyond the last watermark.
Includes file-stability checking to avoid reading a CSV mid-write or
while locked by another program (e.g. open in Excel).
"""

import time
from pathlib import Path

import pandas as pd

from app.core.logging_setup import get_logger
from app.core.models import SourceConfig, SourceType, MetricMode
from app.extract.base_extractor import AbstractExtractor

logger = get_logger(__name__)


class FileNotStableError(Exception):
    """Raised when a CSV file could not be safely read (locked or mid-write)."""
    pass


class CSVExtractor(AbstractExtractor):
    """
    Concrete extractor for local CSV files.

    NOTE (known limitation): assumes strictly append-only CSVs.
    See KNOWN_LIMITATIONS.md.
    """

    def __init__(self, stability_check_interval: float = 2.0, max_retries: int = 3):
        self.stability_check_interval = stability_check_interval
        self.max_retries = max_retries

    def _is_file_stable(self, path: Path) -> bool:
        try:
            size_before = path.stat().st_size
            mtime_before = path.stat().st_mtime
        except FileNotFoundError:
            raise

        time.sleep(self.stability_check_interval)

        size_after = path.stat().st_size
        mtime_after = path.stat().st_mtime

        return size_before == size_after and mtime_before == mtime_after

    def _wait_for_stable_file(self, file_path: str) -> None:
        path = Path(file_path)

        for attempt in range(1, self.max_retries + 1):
            try:
                if self._is_file_stable(path):
                    logger.debug("File '%s' is stable (attempt %d).", file_path, attempt)
                    return
                logger.warning(
                    "File '%s' appears to be changing (attempt %d/%d). Retrying...",
                    file_path, attempt, self.max_retries,
                )
            except PermissionError:
                logger.warning(
                    "File '%s' is locked by another program (attempt %d/%d). Retrying...",
                    file_path, attempt, self.max_retries,
                )

        raise FileNotStableError(
            f"File '{file_path}' did not stabilize after {self.max_retries} attempts "
            f"(possibly locked or being actively written to)."
        )

    def read_csv(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        self._wait_for_stable_file(file_path)

        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=True)
        except PermissionError as e:
            raise FileNotStableError(
                f"File '{file_path}' is locked by another program: {e}"
            )

        df = self._normalize_headers(df)
        logger.debug("Read %d total rows from %s", len(df), file_path)
        return df

    def _normalize_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        cleaned = {col: " ".join(col.split()) for col in df.columns}
        return df.rename(columns=cleaned)

    def _expected_columns(self, source_config: SourceConfig) -> list[str]:
        expected: list[str] = []

        if source_config.source_type == SourceType.EVENT:
            expected.append(source_config.id_column)
            expected.append(source_config.date_column)
            if source_config.column_mapping:
                expected.extend(source_config.column_mapping.values())

        elif source_config.source_type == SourceType.METRIC:
            expected.append(source_config.date_column)

            if source_config.metric_mode == MetricMode.WIDE:
                expected.extend(source_config.metric_columns)

            elif source_config.metric_mode == MetricMode.LONG:
                expected.append(source_config.dimension_column)
                expected.append(source_config.value_column)
                if source_config.rank_column:
                    expected.append(source_config.rank_column)
                if source_config.row_key_column:
                    expected.append(source_config.row_key_column)

        return expected

    def _validate_columns(self, df: pd.DataFrame, source_config: SourceConfig) -> None:
        expected = self._expected_columns(source_config)
        missing = [col for col in expected if col not in df.columns]

        if missing:
            raise ValueError(
                f"Source '{source_config.source_name}': missing expected column(s) "
                f"{missing} in file '{source_config.file_path}'. "
                f"Found columns: {list(df.columns)}"
            )

    def extract(self, source_config: SourceConfig, last_watermark: int) -> pd.DataFrame:
        df = self.read_csv(source_config.file_path)
        self._validate_columns(df, source_config)

        total_rows = len(df)

        if last_watermark >= total_rows:
            logger.info(
                "No new rows for '%s' (watermark=%d, total_rows=%d)",
                source_config.source_name, last_watermark, total_rows,
            )
            return df.iloc[0:0]

        new_rows = df.iloc[last_watermark:].reset_index(drop=True)
        logger.info(
            "Extracted %d new row(s) for '%s' (watermark=%d -> %d)",
            len(new_rows), source_config.source_name, last_watermark, total_rows,
        )
        return new_rows